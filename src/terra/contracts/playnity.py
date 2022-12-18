import logging
from terra import util_terra

from common.make_tx import (
    make_reward_tx,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)

    print(f"PlayNity!")
    return True


def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)

