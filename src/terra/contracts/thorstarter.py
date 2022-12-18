from terra import util_terra
from terra.make_tx import (
    make_swap_tx_terra,
)

IDO = {
    # Luart IDO
    "terra10f7w8d5kdzwhlclyk73j887ws8r35972kgzusx": {
        "currency": "LUART",
        "price_per_token": 0.025,
    }
}

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "join_ido" in execute_msg:
        return False

    if "deposit" in execute_msg:
        return handle_ido_deposit(exporter, elem, txinfo, index)

    print(f"Thorstarter!")
    return True


def handle_ido_deposit(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    contract = elem["tx"]["value"]["msg"][index]["value"]["contract"]

    assert(contract in IDO)
    ido_price = IDO[contract]["price_per_token"]
    received_currency = IDO[contract]["currency"]

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    received_amount = sent_amount / ido_price

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)
