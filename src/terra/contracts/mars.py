from terra import util_terra
from terra.make_tx import (
    make_stake_tx,
    make_unstake_tx,
    make_deposit_collateral_tx,
    make_withdraw_collateral_tx,
)
from terra.col4 import (
    handle_lp,
)
from common.make_tx import (
    make_just_fee_tx,
    make_borrow_tx,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    #if "swap" in execute_msg:
    #    return handle_swap(exporter, elem, txinfo, index)

    # lockdrop
    if "deposit_ust" in execute_msg:
        return handle_deposit_ust(exporter, elem, txinfo, index)
    if "withdraw_ust" in execute_msg:
        return handle_withdraw_ust(exporter, elem, txinfo, index)

    if "deposit_native" in execute_msg:
        return handle_deposit_native(exporter, elem, txinfo, index)

    if "update_position" in execute_msg:
        return handle_update(exporter, elem, txinfo, index)

    if "borrow" in execute_msg:
        return handle_borrow(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "stake" in msg:
            return handle_stake(exporter, elem, txinfo, index)


    print("Mars!")
    return True

def handle_update(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = util_terra._execute_msg(elem, index)

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    print("TODO")
    #quit()

def handle_borrow(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = util_terra._execute_msg(elem, index)

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    borrow_amount, borrow_currency = util_terra._convert(*transfers_in[0])
    row = make_borrow_tx(txinfo, borrow_amount, borrow_currency)
    exporter.ingest_row(row)

def handle_deposit_native(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = util_terra._execute_msg(elem, index)

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    row = make_deposit_collateral_tx(txinfo, sent_amount, sent_currency)
    exporter.ingest_row(row)

def handle_withdraw_ust(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = util_terra._execute_msg(elem, index)

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    assert(len(transfers_out) == 0)

    amount, currency = util_terra._convert(*transfers_in[0])
    row = make_unstake_tx(txinfo, amount, currency)
    duration = msg["withdraw_ust"]["duration"]
    row.comment += f" *was locked for {duration} month"
    exporter.ingest_row(row)
def handle_deposit_ust(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = util_terra._execute_msg(elem, index)

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])
    row = make_stake_tx(txinfo, amount, currency)
    if "duration" in msg["deposit_ust"]:
        duration = msg["deposit_ust"]["duration"]
        row.comment += f" *locked for {duration} month"
    else:
        row.comment += f" *locked in MARS-UST pool"
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