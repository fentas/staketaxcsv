import logging
from terra import util_terra

from terra.make_tx import (
    make_swap_tx_terra,
    make_submit_limit_order,
)

from terra.col4.handle_lp import handle_lp_deposit, handle_lp_withdraw


def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    
    if "assert_limit_order" in execute_msg:
        return handle_assert_limit_order(exporter, elem, txinfo, index)

    if "swap" in execute_msg:
        return handle_swap(exporter, elem, txinfo, index)

    if "provide_liquidity" in execute_msg:
        return handle_lp_deposit(exporter, elem, txinfo, index)

    if "execute_swap_operations" in execute_msg:
        return handle_swap(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        if "swap" in msg:
            return handle_swap(exporter, elem, txinfo, index)

        if "withdraw_liquidity" in msg:
            return handle_lp_withdraw(exporter, elem, txinfo, index)

        if "execute_swap_operations" in msg:
            return handle_swap(exporter, elem, txinfo, index)

    print('TerraSwap!')
    quit()
    return True

def handle_assert_limit_order(exporter, elem, txinfo, index):
    ask_amount = ""
    ask_currency = ""
    offer_amount = ""
    offer_currency = ""
    row = make_submit_limit_order(txinfo, ask_amount, ask_currency, offer_amount, offer_currency)
    exporter.ingest_row(row)

def handle_swap(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1 and len(transfers_out) == 1)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)

def handle_swap(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    assert(len(transfers_out) == 1)

    offer_amount, offer_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    exporter.ingest_row(row)