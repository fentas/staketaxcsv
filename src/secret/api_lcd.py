import logging
import math
import time
import json

import requests
# from settings_csv import SECRET_NODE
SECRET_NODE = "https://api-secret.cosmostation.io"
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


def _get_txs(wallet_address, from_id, sleep_seconds):
    uri_path = f"/v1/account/new_txs/{wallet_address}"
    query_params = {
        "limit": LIMIT_PER_QUERY,
        "from": from_id,
    }

    data = _query(uri_path, query_params, sleep_seconds)
    return data


def get_txs(wallet_address, from_id=0, sleep_seconds=1):
    data = _get_txs(wallet_address, from_id, sleep_seconds)

    elems = [{**tx["header"], **tx["data"]} for tx in data]
    # No results or error
    if len(elems) == 0:
        return [], None, 0
    
    total_count = 0
    from_id = elems[-1]["id"] if len(elems) == LIMIT_PER_QUERY else None
    return elems, from_id, total_count
