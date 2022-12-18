import logging
from terra import util_terra
from terra.make_tx import (
    make_swap_tx_terra,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "execute_swap_operations" in execute_msg:
        return handle_swap(exporter, elem, txinfo, index)

    print(f"Coinhall")
    return True


def handle_swap(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_in) >= 1)
    assert(len(transfers_out) == 1)

    offer_amount, offer_currency = util_terra._convert(*transfers_out[0])

    received_amount = 0
    received_currency = ""

    # sum up
    for transfer in transfers_in:
        amount, currency = util_terra._convert(*transfer)
        assert(received_currency == "" or received_currency == currency)
        received_currency = currency
        received_amount += amount

    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    exporter.ingest_row(row)