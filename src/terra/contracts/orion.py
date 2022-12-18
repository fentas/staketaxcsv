import logging
from terra import util_terra

from terra.make_tx import (
    make_stake_tx,
    make_unstake_tx,
)
from common.make_tx import (
    make_just_fee_tx, 
    make_just_fee_txinfo,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "unbond_init" in execute_msg:
        return handle_fee(exporter, txinfo, "init unbond")

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "bond" in msg:
            return handle_stake(exporter, elem, txinfo, index)

    print("Orion!")
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_stake(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])
    row = make_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)