"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import time
from urllib.parse import urlencode

from common.CacheChain import CacheChain
import requests
from settings_csv import TERRA_LCD_NODE


class LcdAPI:
    session = requests.Session()

    @classmethod
    def contract_info(cls, contract):
        cache = CacheChain()
        if cache is not None:
            data = cache.get_contract(contract)
            if data is not None:
                return data
            
        uri = f"/wasm/contracts/{contract}"
        logging.info("Querying lcd for contract = %s ...", contract)
        data = cls._query(uri, {})

        #response = requests.get(url)
        #data = response.json()
        #time.sleep(0.1)

        if cache is not None:
            data = cache.set_contract(contract, data)

        return data

    @classmethod
    def _query(cls, uri_path, query_params, sleep_seconds=1):
        url = f"{TERRA_LCD_NODE}{uri_path}"
        logging.info("Requesting url %s?%s", url, urlencode(query_params))
        response = cls.session.get(url, params=query_params)

        time.sleep(sleep_seconds)
        return response.json()
