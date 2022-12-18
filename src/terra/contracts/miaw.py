import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)
from terra.make_tx import (
    make_swap_tx_terra,
    make_submit_limit_order,
)
from common.make_tx import (
    make_just_fee_tx,
    make_just_fee_txinfo,
)
from terra.col4.handle_lp import handle_lp_stake, handle_lp_unstake

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "execute_order" in execute_msg:
        return handle_execute(exporter, elem, txinfo, index)

    if "submit_order" in execute_msg:
        return handle_submit_order(exporter, elem, txinfo, index)

    if "cancel_order" in execute_msg:
        return handle_fee(exporter, txinfo, "cancel order")


    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "bond" in msg:
            return handle_lp_stake(exporter, elem, txinfo, index)

    quit()
    print('Miaw!')
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_submit_order(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    # actual trade
    offer_amount, offer_currency = util_terra._amount(events["offer_asset"][0])
    ask_amount, ask_currency = util_terra._amount(events["ask_asset"][0])

    row = make_submit_limit_order(txinfo, ask_amount, ask_currency, offer_amount, offer_currency)
    exporter.ingest_row(row)

# https://github.com/miaw-team/miaw-limit-order/blob/933b4a5e14b70ae49192b88e397b9b8199c3cfda/src/order.rs#L187
# terra finder and et shows wrong result:
# shows actual swap but the excess_amount is transferred to executer as boni
# so it can be calculated as fee? :P
def handle_execute(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    # as we factor in excess amount fee
    # we use the swap amount not the actual returned amount
    received_amount, received_currency = util_terra._convert(*transfers_in[0])
    received_amount = util_terra._float_amount(events["return_amount"][0], received_currency)
    
    # actual trade
    offer_currency = util_terra._asset_to_currency(events["offer_asset"][0], txid)
    offer_amount = util_terra._float_amount(events["offer_amount"][0], offer_currency)
    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    row.comment = " - [miaw] limit order execute"
    exporter.ingest_row(row)

    # fee's in Miaw Token
    fee_currency = "MIAW"
    fee_amount = util_terra._float_amount(events["offer_amount"][0], fee_currency)
    row = make_just_fee_tx(txinfo, fee_amount, fee_currency)
    row.comment = " - [miaw] execution fee"
    exporter.ingest_row(row)

    # excess amount fee
    if "excess_amount" in events:
        excess_amount = util_terra._float_amount(events["excess_amount"][0], received_currency)
        row = make_just_fee_tx(txinfo, excess_amount, received_currency)
        row.comment = " - [miaw] excess amount fee"
        exporter.ingest_row(row)