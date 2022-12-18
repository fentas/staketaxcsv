"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import time
from urllib.parse import urlencode

from datetime import datetime
from common.CacheChain import CacheChain
import requests

COINHALL_API = "https://api.coinhall.org/api/v1/charts/terra/candles"

PAIRS = {
    "LUNA": "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6",
    "BLUNA": "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6",
    "NLUNA": "terra1tndcaqxkpc5ce9qee5ggqf430mr2z3pefe5wj6",
    "ANC": "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
    "ANC": "terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
    "MINE": "terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz",
    "SPEC": "terra1tn8ejzw8kpuc87nu42f6qeyen4c7qy35tl8t20",
    "LOOPR": "terra1dw5j23l6nwge69z0enemutfmyc93c36aqnzjj5",
    "LOOP": "terra106a00unep7pvwvcck4wylt4fffjhgkf9a0u6eu",
    "PSI": "terra163pkeeuwxzr0yhndf8xd2jprm9hrtk59xf7nqf",
    "KUJI": "terra1zkyrfyq7x9v5vqnnrznn3kvj35az4f6jxftrl2",
    "APOLLO": "terra1xj2w7w8mx6m2nueczgsxy2gnmujwejjeu2xf78",
    "ASTRO": "terra1l7xu2rl3c7qmtx3r5sd2tz25glf6jh8ul7aag7",
    "GLOW": "terra1p44kn7l233p7gcj0v3mzury8k7cwf4zt6gsxs5",
    "WHALE": "terra1v4kpj65uq63m4x0mqzntzm27ecpactt42nyp5c",
    "XDEFI": "terra1476fucrvu5tuga2nx28r3fctd34xhksc2gckgf",
    "NETH": "terra14fyt2g3umeatsr4j4g2rs8ca0jceu3k0mcs7ry",
    "BETH": "terra14fyt2g3umeatsr4j4g2rs8ca0jceu3k0mcs7ry",
    "PRISM": "terra19d2alknajcngdezrdhq40h6362k92kz23sz62u",
    "XPRISM": "terra19d2alknajcngdezrdhq40h6362k92kz23sz62u",
    "TWD": "terra1etdkg9p0fkl8zal6ecp98kypd32q8k3ryced9d",
    "METH": "terra14fyt2g3umeatsr4j4g2rs8ca0jceu3k0mcs7ry",
    "MAMD": "terra18cxcwv0theanknfztzww8ft9pzfgkmf2xrqy23",
    "MTSLA": "terra1pdxyk2gkykaraynmrgjfq2uu7r9pf5v8x7k4xk",
    "MUSO": "terra1zey9knmvs2frfrjnf4cfv4prc4ts3mrsefstrj",
    "MSLV": "terra1f6d9mhrsl5t6yxqnr4rgfusjlt3gfwxdveeyuy",
    "MQQQ": "terra1dkc8075nv34k2fu6xn6wcgrqlewup2qtkr4ymu",
    "MCOIN": "terra1h7t2yq00rxs8a78nyrnhlvp0ewu8vnfnx5efsl",
    "MDOT": "terra17rvtq0mjagh37kcmm4lmpz95ukxwhcrrltgnvc",
    "MARKK": "terra1a5cc08jt5knh0yx64pg6dtym4c4l8t63rhlag3",
    "MSQ": "terra1u3pknaazmmudfwxsclcfg3zy74s3zd3anc5m52",
    "MIR": "terra1amv303y8kzxuegvurh0gug2xe9wkgj65enq2ux",
    "LUART": "terra1m9hm6cxlf0907yy7lsssyfpzswlu54r99k9dxf",
    "ORION": "terra1z6tp0ruxvynsx5r9mmcc2wcezz9ey9pmrw5r8g",
    "HALO": "terra1yjg0tuhc6kzwz9jl8yqgxnf2ctwlfumnvscupp",
    "TLAND": "terra1jzqlw8mfau9ewr7lufqkrpgfzk4legz9zx306p",
    "VKR": "terra1e59utusv5rspqsu8t37h5w887d9rdykljedxw0",
    "PLY": "terra19fjaurx28dq4wgnf9fv3qg0lwldcln3jqafzm6",
    "STT": "terra19pg6d7rrndg4z4t0jhcd7z9nhl3p5ygqttxjll",
    "SDOLLAR": "terra1fmv3g96s4xc9nrnlkdn87vxyaydd22xsxzel5r",
    "LOTA": "terra1pn20mcwnmeyxf68vpt3cyel3n57qm9mp289jta",
    "LUNAX": "terra1llhpkqd5enjfflt27u3jx0jcp5pdn6s9lfadx3",
    "MIAW": "terra12mzh5cp6tgc65t2cqku5zvkjj8xjtuv5v9whyd",
    "ATLO": "terra1ycp5lnn0qu4sq4wq7k63zax9f05852xt9nu3yc",
    "BPSIDP-24M": "terra1svequ729grnrj2d8x609e45axajrdjz87athfh",
    "ROWAN": "terra1vnpmtslwxr76ar3wmjy8jlp6c5y0sckvh96esl",
    "ALTE": "terra18adm0emn6j3pnc90ldechhun62y898xrdmfgfz",
    "MARS": "terra19wauh79y42u5vt62c5adt2g5h4exgh26t3rpds",
    "ROBO": "terra1sprg4sv9dwnk78ahxdw78asslj8upyv9lerjhm",
    "YLUNA": "terra1kqc65n5060rtvcgcktsxycdt2a4r67q2zlvhce",
    "PLUNA": "terra1persuahr6f8fm6nyup0xjc7aveaur89nwgs5vs",
}

IGNORE = ["UST", "AUST", "SEK", "SDR", "MNT", "KRT", "IDR", "EUR", "AUD", "THB", "NOK", "JPY", "IDR", "INR", "GBP", "DKK", "CHF", "PHP",
"CAD", "CNY", "SGD", "HKD", "MYR", 
"SCRT", "OSMO", "PYLONDP", "ART", "VVP"]

class Coinhall:
    session = requests.Session()

    @classmethod
    def price(cls, contract, date):
        contract = contract.upper()
        if contract == "" or contract.startswith("TERRA") or contract in IGNORE:
            return None


        if contract not in PAIRS:
            print(f"MISSING CONTRACT PAIR: {contract}")
            return None

        timestamp = int(datetime.strptime(date.split(' ')[0], "%Y-%m-%d").timestamp()) + 43200
        contract = PAIRS[contract]

        cache = CacheChain()
        if cache is not None:
            data = cache.get_price(contract, timestamp)
            if data is not None:
                return data
        
        if contract in ["yLuna", "pLuna"]:
            prism = self.price("PRISM", timestamp)
            data = self.price(contract, timestamp)

            for k in ["open", "high", "low", "close"]:
                data[k] = prism[k] * data[k]
        else:
            uri = f"?bars=1&from={timestamp}&to={timestamp}&quoteAsset=uusd&interval=1d&pairAddress={contract}"
            data = cls._query(uri, {})
            if len(data) != 1:
                print("Coinhall wrong response")
                print(f"{COINHALL_API}{uri}")
                print(data)
                return None
            data = data[0]

        if cache is not None:
            data = cache.set_price(contract, timestamp, data)

        return data

    @classmethod
    def _query(cls, uri_path, query_params, sleep_seconds=1):
        url = f"{COINHALL_API}{uri_path}"
        logging.info("Requesting url %s", url)
        response = cls.session.get(url)

        time.sleep(sleep_seconds)
        return response.json()
