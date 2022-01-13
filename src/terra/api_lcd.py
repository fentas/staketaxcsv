
"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import requests
import time

from common.CacheChain import CacheChain
from settings_csv import TERRA_LCD_NODE


class LcdAPI:

    @classmethod
    def contract_info(cls, contract):
        cache = CacheChain()
        if cache is not None:
            data = cache.get_contract(contract)
            if data is not None:
                return data
            
        url = "{}/wasm/contracts/{}".format(TERRA_LCD_NODE, contract)

        logging.info("Querying lcd for contract=%s...", contract)
        response = requests.get(url)
        data = response.json()
        time.sleep(0.1)

        if cache is not None:
            data = cache.set_contract(contract, data)

        return data
