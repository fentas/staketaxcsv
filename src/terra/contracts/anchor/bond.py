from common.ErrorCounter import ErrorCounter
from common.make_tx import make_unknown_tx, make_simple_tx
from terra import util_terra
from terra.constants import CUR_BLUNA, CUR_LUNA
from terra.make_tx import make_swap_tx_terra, make_unbond_tx, make_burn_collateral_tx
from common.ExporterTypes import TX_TYPE_BOND

from common.make_tx import make_transfer_in_tx, make_transfer_out_tx

def handle_bond(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get sent amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    sent_amount, sent_currency = transfers_out[0]

    try:
        # Get minted amount of bluna
        received_currency = CUR_BLUNA
        received_amount_string = elem["logs"][index]["events_by_type"]["from_contract"]["minted"][0]
        received_amount = util_terra._float_amount(received_amount_string, CUR_BLUNA)

        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    except Exception:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)
        ErrorCounter.increment("handle_bond_unknown", txid)


def handle_unbond(exporter, elem, txinfo):
    row = make_unbond_tx(txinfo)
    exporter.ingest_row(row)


def handle_unbond_withdraw(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get received amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    received_amount, received_currency = transfers_in[0]

    sent_amount = received_amount
    sent_currency = CUR_BLUNA
    assert(received_currency == CUR_LUNA)

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)


def handle_burn_collateral(exporter, elem, txinfo, index=0):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get received amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_out) == 1)
    amount, currency = util_terra._convert(*transfers_out[0])

    print (amount)
    print(currency)
    # When withdrawing bETH, Anchor will first submit a burn transaction
    if currency == 'BETH':
        row = make_transfer_out_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return

    row = make_unbond_tx(txinfo)
    exporter.ingest_row(row)


def handle_mint_collateral(exporter, elem, txinfo, index=0):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get received amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_in) == 1)
    amount, currency = util_terra._convert(*transfers_in[0])

    if currency == 'BETH':
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return
    
    quit()
    # Minting bETH collateral
    row = make_simple_tx(txinfo, TX_TYPE_BOND)
    exporter.ingest_row(row)
