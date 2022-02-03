import logging
import math
import time
import json

import requests
from settings_csv import SECRET_NODE

LIMIT_PER_QUERY = 50


def _query(uri_path, query_params, sleep_seconds=1):
    url = f"{SECRET_NODE}{uri_path}"
    response = requests.get(url, query_params)
    logging.info("requested url=%s", response.url)

    time.sleep(sleep_seconds)
    return response.json()


def get_tx(txid):
    uri_path = f"/v1/tx/hash/{txid}"
    data = _query(uri_path, {})
    return {**data["header"], **data["data"]}


def _get_txs(wallet_address, offset, sleep_seconds):
    uri_path = f"/v1/account/new_txs/{wallet_address}"
    query_params = {
        "limit": LIMIT_PER_QUERY,
        "from": offset,
    }

    data = _query(uri_path, query_params, sleep_seconds)
    return data


def get_txs(wallet_address, offset=0, sleep_seconds=1):
    data = _get_txs(wallet_address, offset, sleep_seconds)

    elems = [{**tx["header"], **tx["data"]} for tx in data]
    # No results or error
    if len(elems) == 0:
        return [], None, 0
    
    total_count = 0
    next_offset = offset + LIMIT_PER_QUERY
    return elems, next_offset, total_count
