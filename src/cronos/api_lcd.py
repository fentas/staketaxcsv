import logging
import math
import time
import json

import requests
from settings_csv import CRONOS_NODE

LIMIT_PER_QUERY = 50


def _query(uri_path, query_params, sleep_seconds=1):
    url = f"{CRONOS_NODE}{uri_path}"
    response = requests.get(url, query_params)
    logging.info("requested url=%s", response.url)

    time.sleep(sleep_seconds)
    return response.json()


def get_tx(txid):
    uri_path = f"/v1/transactions/{txid}"
    data = _query(uri_path, {})
    elem = data.get("result", None)
    _post_process_tx(elem)
    return elem


def _get_txs(wallet_address, offset, sleep_seconds):
    uri_path = f"/v1/accounts/{wallet_address}/transactions"
    query_params = {
        "limit": LIMIT_PER_QUERY,
        "pagination": "offset",
        "page": offset,
        "order": "height.desc",
    }

    data = _query(uri_path, query_params, sleep_seconds)
    return data


def get_txs(wallet_address, offset=1, sleep_seconds=1):
    data = _get_txs(wallet_address, offset, sleep_seconds)

    elems = data["result"]
    # No results or error
    if len(elems) == 0:
        return [], None, 0
    
    # Convert log string to dict
    for elem in elems:
        _post_process_tx(elem)

    total_count = int(data["pagination"]["total_page"])
    next_offset = offset +1 if total_count > offset else None
    return elems, next_offset, total_count


def _post_process_tx(elem):
    elem["logs"] = []
    if elem["log"].startswith('['):
        elem["logs"] = json.loads(elem["log"])
