from terra import util_terra
from terra.make_tx import (
    make_nft_buy_tx,
)

"""
  "name": "Intergalactic Planetary",
  "symbol": "IGPT",
  "admin": "terra18hh9t4fdzpwruzkjmguf6w8lf7n062dxz2zj25",
  "whitelist_mint_time": 1639526400,
  "open_mint_time": 1639785600,
  "merkle_root": "f0302d9a24e51f77b1f7a3e3b924d88a3c14916c541846641b786059a2650962",
  "denom": "uusd",
  "price": 25000000,
  "max_issuance": 5000,
  "token_uri": "ipfs://Qmc8nKmttf5EHAiDSy1huoJqnYKVg58dLwmNV8TQHhQnrN"

"""
NAME = "Intergalactic Planetary"
CONTRACT_ADDR = "terra1p82qdq4gy9wskw9tvy3f5g4ujh6fxjmm9zzhzx"

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "mint" in execute_msg:
        return handle_mint(exporter, elem, txinfo, index)

    print(NAME)
    return True

def handle_mint(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)
    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    token_id = events["token_id"][0]
    nft_currency = "{}_{}".format(CONTRACT_ADDR, token_id)
    row = make_nft_buy_tx(txinfo, sent_amount, sent_currency, nft_currency, NAME)
    exporter.ingest_row(row)