""" Parsing and utility functions for fcd tx info """

import base64
import json
import logging

from settings_csv import TERRA_LCD_NODE
from terra.api_lcd import LcdAPI
from terra.config_terra import localconfig
import common.ibc.api_lcd

from terra.constants import (
    SPECIAL_CURRENCY
)


def _contracts(elem):
    out = []

    count = len(elem["tx"]["value"]["msg"])
    for i in range(count):
        out.append(_contract(elem, i))
    return out


def _contract(elem, index=0):
    msg = elem["tx"]["value"]["msg"][index]
    return msg["value"].get("contract", None)


def _any_contracts(addrs, elem):
    contracts = set([c for c in _contracts(elem) if c is not None])
    return len(set(addrs).intersection(contracts)) > 0


def _execute_msgs(elem):
    out = []

    count = len(elem["tx"]["value"]["msg"])
    for i in range(count):
        out.append(_execute_msg(elem, i))
    return out


def _execute_msgs_keys(elem):
    msgs = _execute_msgs(elem)
    out = []
    for msg in msgs:
        keys = list(msg.keys())

        if len(keys) == 1:
            out.append(keys[0])
        else:
            out.append(None)
    return out


def _execute_msg(elem, index=0):
    msg = _execute_msg_field(elem, index)
    if "ledger_proxy" in msg and "msg" in msg["ledger_proxy"]:
        return msg["ledger_proxy"]["msg"]
    return msg


def _execute_msg_field(elem, index=0):
    msg_base64 = elem["tx"]["value"]["msg"][index]["value"]["execute_msg"]

    if type(msg_base64) is str:
        try:
            msg = json.loads(msg_base64)
            return msg
        except Exception:
            pass

    if type(msg_base64) is dict:
        for k, v in msg_base64.items():
            if "msg" in v:
                try:
                    # brute force decode msg - somtimes it is base64 decoded
                    msg_base64[k]["msg"] = json.loads(base64.b64decode(v["msg"]))
                except Exception:
                    pass
        return msg_base64

    msg = msg_base64
    try:
        msg = base64.b64decode(msg_base64)
    except Exception:
        pass
    msg = json.loads(msg)

    for k, v in msg.items():
        if "msg" in v:
            try:
                msg[k]["msg"] = json.loads(base64.b64decode(v["msg"]))
            except UnicodeDecodeError as e:
                msg[k]["msg"] = {"error_decoding": {}}

    return msg


def _multi_transfers(elem, wallet_address, txid):
    transfers_in = []
    transfers_out = []

    for log_index, log in enumerate(elem["logs"]):
        events = elem["logs"][log_index].get("events", [])
        for event in events:
            if event["type"] == "message":
                attributes = event["attributes"]
                for i in range(0, len(attributes)):
                    if attributes[i]["key"] == "sender":
                        sender = attributes[i]["value"]

            if event["type"] == "transfer":
                attributes = event["attributes"]

                for i in range(0, len(attributes), 2):
                    recipient = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]

                    if recipient == wallet_address:
                        amount, currency = _amount(amount_string)
                        transfers_in.append([amount, currency])
                    elif sender == wallet_address:
                        amount, currency = _amount(amount_string)
                        transfers_out.append([amount, currency])
    return transfers_in, transfers_out


def _transfers(elem, wallet_address, txid, multicurrency=False, index=None):
    transfers_in = []
    transfers_out = []
    is_columbus_3 = (elem.get("chainId", None) == "columbus-3")
    if is_columbus_3:
        return _transfers_columbus_3(elem, wallet_address, txid, multicurrency)
    logs = elem["logs"]

    if index is not None:
        logs = [logs[index]]
    
    for log in logs:
        cur_transfers_in, cur_transfers_out = _transfers_log(log, wallet_address, multicurrency)
        transfers_in.extend(cur_transfers_in)
        transfers_out.extend(cur_transfers_out)

    return transfers_in, transfers_out


def _transfers_log(log, wallet_address, multicurrency=False, from_contract=False):
    transfers_in = []
    transfers_out = []
    events = log.get("events", [])

    # check message if multisend
    multisend = False
    sender = ""
    steps = 3
    for event in events:
        if event["type"] == "message":
            if event["attributes"][0]["value"] == "/cosmos.bank.v1beta1.MsgMultiSend":
                multisend = True
                sender = event["attributes"][1]["value"]
                steps = 2
            break

    for event in events:
        if event["type"] == "transfer":
            attributes = event["attributes"]

            for i in range(0, len(attributes), steps):
                recipient = ""
                amount_string = ""
                if multisend:
                    recipient = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]
                else:
                    recipient = attributes[i]["value"]
                    sender = attributes[i + 1]["value"]
                    amount_string = attributes[i + 2]["value"]

                    # sometimes with multiswaps
                    # there are swaps for none
                    if amount_string == "":
                        amount_string = "0uluna"

                if recipient == wallet_address:
                    if multicurrency:
                        for amount, currency in _amounts(amount_string):
                            transfers_in.append([amount, currency])
                    else:
                        amount, currency = _amount(amount_string)
                        transfers_in.append([amount, currency])
                elif sender == wallet_address:
                    if multicurrency:
                        for amount, currency in _amounts(amount_string):
                            transfers_out.append([amount, currency])
                    else:
                        amount, currency = _amount(amount_string)
                        transfers_out.append([amount, currency])
    
    #if len(transfers_in) == 0 and len(transfers_out) == 0 or from_contract:
    for event in events:
        if event["type"] == "from_contract":
            attributes = event["attributes"]

            for i in range(0, len(attributes), 1):
                attribute = attributes[i]

                if attribute["key"] == "action" and attribute["value"] in ["transfer", "send", "burn_from"]:
                    currency = attributes[i-1]["value"]
                    sender = attributes[i+1]["value"]
                    recipient = attributes[i+2]["value"]
                    amount = attributes[i+3]["value"]

                    if recipient == wallet_address:
                        transfers_in.append([amount, currency])
                    elif sender == wallet_address:
                        transfers_out.append([amount, currency])

                if attribute["key"] == "action" and attribute["value"] in ["mint"]:
                    currency = attributes[i-1]["value"]
                    to = attributes[i+1]["value"]
                    amount = attributes[i+2]["value"]

                    if to == wallet_address:
                        transfers_in.append([amount, currency])

                if attribute["key"] == "action" and attribute["value"] in ["burn"]:
                    currency = attributes[i-1]["value"]
                    fro = attributes[i+1]["value"]
                    amount = attributes[i+2]["value"]

                    if fro == wallet_address:
                        transfers_out.append([amount, currency])

                if attribute["key"] == "action" and attribute["value"] in ["transfer_from"]:
                    currency = attributes[i-1]["value"]
                    sender = attributes[i+1]["value"]
                    recipient = attributes[i+2]["value"]
                    amount = attributes[i+4]["value"]

                    if recipient == wallet_address:
                        transfers_in.append([amount, currency])
                    elif sender == wallet_address:
                        transfers_out.append([amount, currency])

    return transfers_in, transfers_out


def _transfers_columbus_3(elem, wallet_address, txid, multicurrency=False):
    transfers_in = []
    transfers_out = []

    for log_index, log in enumerate(elem["logs"]):
        events = elem["logs"][log_index]["events"]

        for event in events:
            if event["type"] == "transfer":
                attributes = event["attributes"]

                for i in range(0, len(attributes), 2):
                    recipient = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]

                    if recipient == wallet_address:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_in.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_in.append([amount, currency])
                    else:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_out.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_out.append([amount, currency])

    return transfers_in, transfers_out


def _extract_amounts(amount_string):
    """
    Example input: '230344ukrw,3uluna,5umnt'
    Example output: { "KRW" : .0230344, "LUNA" : .000003, "MNT" : .00005 }
    """
    if amount_string == "":
        return {}

    out = {}
    amounts = amount_string.split(",")

    for amount in amounts:
        if "terra" in amount:
            # token address (i.e. "766890terra1vxtwu4ehgzz77mnfwrntyrmgl64qjs75mpwqaz")
            uamount, partial_address = amount.split("terra")
            address = "terra{}".format(partial_address)
            currency = _lookup_address(address, "")
            out[currency] = _float_amount(uamount, currency)
        elif "ibc" in amount:
            # ibc token (i.e. "165ibc/0471F1C4E7AFD3F07702BEF6DC365268D64570F7C1FDC98EA6098DD6DE59817B" for osmo)
            uamount, ibc_address = amount.split("ibc")
            ibc_address = "ibc" + ibc_address

            currency = common.ibc.api_lcd.get_ibc_ticker(TERRA_LCD_NODE, ibc_address, localconfig.ibc_addresses)
            out[currency] = _float_amount(uamount, currency)
        else:
            # regular (i.e. 99700703uusd)
            uamount, currency = amount.split("u", 1)
            currency = _currency(currency)
            out[currency] = _float_amount(uamount, currency)

    return out


def _asset_to_currency(asset, txid):
    # Example: 'terra1mqsjugsugfprn3cvgxsrr8akkvdxv2pzc74us7' -> USD
    if asset.startswith("native:"):
        asset = asset[7:]
    elif asset.startswith("cw20:"):
        asset = asset[5:]

    if asset.startswith("terra"):
        currency = _lookup_address(asset, txid)
        return currency

    if asset.startswith("u"):
        return _denom_to_currency(asset)


    raise Exception("_asset_to_currency(): Unable to determine currency for asset={} txid={}".format(
        asset, txid))


def _amounts(amounts_string):
    # Example inputs: '230344ukrw,3uluna,5umnt', '50674299uusd'
    out = []
    amounts = _extract_amounts(amounts_string)
    for currency, amount in amounts.items():
        out.append((amount, currency))

    return out


def _amount(amount_string):
    # Example input: '50674299uusd'

    amounts = _extract_amounts(amount_string)

    currency = list(amounts.keys())[0]
    amount = list(amounts.values())[0]
    return amount, currency


def _float_amount(amount_string, currency):
    # Example input: '50674299' , 'USD'
    return float(amount_string) / 10 ** _decimals(currency)


def _currency(currency_string):
    # Example: 'luna' -> 'LUNA'
    currency_string = currency_string.upper()
    if currency_string == "KRW":
        return "KRT"
    if currency_string == "USD":
        return "UST"
    return currency_string


def _denom_to_currency(denom):
    # Example: 'uluna' -> 'LUNA'
    currency = denom[1:]
    return _currency(currency)


def _decimals(currency):
    if currency in ["LUNA", "UST"]:
        # temporary override fix (symbol clash cases)
        return 6
    elif currency in localconfig.decimals and localconfig.decimals[currency]:
        return int(localconfig.decimals[currency])
    else:
        # default is 6 decimals
        return 6


# https://github.com/terra-project/shuttle
# https://github.com/terra-project/shuttle/blob/main/terra/src/config/TerraAssetInfos.ts
# https://lcd.terra.dev/swagger-ui/#/Wasm/get_wasm_contracts__contractAddress_
def _lookup_address(addr, txid):
    """
    Returns <currency_symbol>.
    Updates cache for localconfig.currency_address, localconfig.decimals.
    """
    #if addr in localconfig.currency_addresses:
    #    return localconfig.currency_addresses[addr]

    init_msg = _query_wasm(addr)
    #logging.info("init_msg: %s", init_msg)

    if addr in SPECIAL_CURRENCY:
        return SPECIAL_CURRENCY[addr]

    if "symbol" in init_msg:
        currency = init_msg["symbol"]

        if currency == "uLP":
            currency = _lookup_lp_address(addr, txid)

        decimals = int(init_msg["decimals"])

        # Cache result
        localconfig.currency_addresses[addr] = currency
        localconfig.decimals[currency] = decimals

        #logging.info("Found symbol=%s decimals=%s", currency, decimals)
        return currency
    elif "terraswap_factory" in init_msg:
        localconfig.currency_addresses[addr] = None
        return None
    else:
        localconfig.currency_addresses[addr] = ""
        raise Exception("Unable to determine currency/swap pair for addr=%s, txid=%s", addr, txid)


def _lookup_lp_address(addr, txid):
    """ Returns symbol for lp currency address """
    if addr in localconfig.lp_currency_addresses:
        return localconfig.lp_currency_addresses[addr]

    init_msg = _query_wasm(addr)
    logging.info("init_msg: %s, txid:%s", init_msg, txid)

    if "init_hook" in init_msg:
        address_for_pair = init_msg["init_hook"]["contract_addr"]
        currency1, currency2 = _query_lp_address(address_for_pair, txid)
    elif "staking_token" in init_msg:
        staking_token = init_msg["staking_token"]
        init_msg = _query_wasm(staking_token)
        address_for_pair = init_msg["init_hook"]["contract_addr"]
        currency1, currency2 = _query_lp_address(address_for_pair, txid)
    elif "mint" in init_msg:
        address_for_pair = init_msg["mint"]["minter"]
        currency1, currency2 = _query_lp_address(address_for_pair, txid)
    elif "mirror_token" in init_msg:
        currency1 = "UST"
        currency2 = "MIR"
    else:
        raise Exception("(1) Unable to determine lp currency for addr={}, txid={}".format(addr, txid))

    if currency1 == "UST":
        lp_currency = "LP_{}_UST".format(currency2)
    elif currency2 == "UST":
        lp_currency = "LP_{}_UST".format(currency1)
    elif currency1 and currency2:
        lp_currency = "LP_{}_{}".format(currency1, currency2)
    else:
        localconfig.currency_addresses[addr] = ""
        raise Exception("(2) Unable to determine lp currency for addr={}, txid={}".format(addr, txid))

    localconfig.lp_currency_addresses[addr] = lp_currency
    return lp_currency


def _query_lp_address(addr, txid):
    """ Queries lp currency address and returns [currency1, currency2] """
    init_msg = _query_wasm(addr)
    logging.info("init_msg: %s", init_msg)

    if "asset_infos" in init_msg:
        out = [None, None]

        # Swap contract pair address
        for i, asset_info in enumerate(init_msg["asset_infos"]):
            if "token" in asset_info:
                contract_addr = asset_info["token"]["contract_addr"]
                init_msg2 = _query_wasm(contract_addr)
                currency = init_msg2["symbol"]
                out[i] = currency
            elif "native_token" in asset_info:
                currency = _denom_to_currency(asset_info["native_token"]["denom"])
                out[i] = currency
            elif "cw20" in asset_info:
                contract_addr = asset_info["cw20"]
                init_msg2 = _query_wasm(contract_addr)
                currency = init_msg2["symbol"]
                out[i] = currency
            elif "native" in asset_info:
                currency = _denom_to_currency(asset_info["native"])
                out[i] = currency
            else:
                raise Exception("Unexpected data for asset_infos", addr, txid, init_msg)

        if out[0] is None or out[1] is None:
            raise Exception("Unable to determine swap pair", txid, init_msg)

        return out
    else:
        localconfig.lp_currency_addresses[addr] = ""
        raise Exception("Unable to determine currency/swap pair for addr=%s, txid=%s", addr, txid)


def _query_wasm(addr):
    # if addr == "terra17y9qkl8dfkeg4py7n0g5407emqnemc3yqk5rup":
        # quit()
    data = LcdAPI.contract_info(addr)

    init_msg = _init_msg(data)
    return init_msg


def _init_msg(data):
    init_msg_base64 = data["result"]["init_msg"]
    if type(init_msg_base64) is dict:
        return init_msg_base64

    init_msg = json.loads(base64.b64decode(init_msg_base64))
    return init_msg


def _event_with_action(elem, event_type, action, index=None):
    logs = elem["logs"]
    
    if index is not None:
        logs = [logs[index]]

    for log in logs:
        event = log["events_by_type"].get(event_type, None)
        if event:
            if action in event["action"]:
                return event
    return None


def _events_with_action(elem, event_type, action, index=None):
    events = []
    logs = elem["logs"]

    if index != None:
        logs = [logs[index]]

    for log in logs:
        event = log["events_by_type"].get(event_type, None)
        if event:
            if action in event["action"]:
                events.append(event)
    return events


def _ingest_rows(exporter, rows, comment=None):
    for i, row in enumerate(rows):
        if comment:
            row.comment = comment
        if i > 0:
            row.fee, row.fee_currency = "", ""
        exporter.ingest_row(row)


def _add_anchor_fees(elem, txid, row):
    # Extract fee, if any, paid by anchor market contract to fee collector
    fee_collector_address = "terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa"
    fee_transfers_in, _ = _transfers(elem, fee_collector_address, txid)

    if len(fee_transfers_in) > 0:
        fee_amount, fee_currency = fee_transfers_in[0]
        row.fee += fee_amount

    return row

def _convert(amount, currency):
    if currency.startswith("terra"):
        currency = _lookup_address(currency, "")
        amount = _float_amount(amount, currency)

    return amount, currency