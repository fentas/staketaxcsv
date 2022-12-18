from terra import util_terra
from terra.make_tx import (
    make_swap_tx_terra,
)
from common.make_tx import (
    make_just_fee_tx,
)
from terra.col4 import (
    handle_simple,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)


ATLO_IDO_PRICE = 0.07

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "claim_whitelist" in execute_msg:
        return
    if "register_vesting_accounts" in execute_msg:
        return False
    if "update_members" in execute_msg:
        return False

    if "register" in execute_msg:
        return handle_ido_register(exporter, elem, txinfo, index)

    if "deposit" in execute_msg:
        return handle_deposit(exporter, elem, txinfo, index)

    if "vote" in execute_msg:
        return handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        #return handle_vote(exporter, elem, txinfo, index)

    print(f"Atlo!")
    return True

def handle_vote(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = txinfo.msgs[index]

    transfers_in, transfers_out = msg.transfers

def handle_deposit(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = txinfo.msgs[index]

    transfers_in, transfers_out = msg.transfers

    assert(len(transfers_out) == 1)
    assert(len(transfers_in) == 0)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    received_amount = sent_amount / ATLO_IDO_PRICE
    received_currency = "ATLO"

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency, empty_fee=True)
    exporter.ingest_row(row)


def handle_ido_register(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)
    assert(len(transfers_in) == 0)

    fee_amount, fee_currency = util_terra._convert(*transfers_out[0])

    row = make_just_fee_tx(txinfo, fee_amount, fee_currency, empty_fee=False)
    row.comment = " *register fee"
    exporter.ingest_row(row)