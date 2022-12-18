import logging
from terra import util_terra
from terra.make_tx import (
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_stake_tx,
)
from terra.col4 import (
    handle_simple,
    handle_reward_contract,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from common.make_tx import make_just_fee_tx

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "deposit" in execute_msg:
        return handle_pool(exporter, elem, txinfo, index)

    print("INK!")
    return True


def handle_pool(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])

    row = make_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)