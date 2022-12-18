import logging
from terra import util_terra
from terra.make_tx import (
    make_lp_stake_tx,
    make_nft_offer_buy_tx,
    make_nft_offer_deposit,
    make_nft_offer_refund,
    make_nft_buy_tx,
)
from terra.col4 import (
    handle_simple,
)
from terra.col4.handle_randomearth import _nft_name
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from common.make_tx import (
    make_just_fee_tx, 
    make_just_fee_txinfo,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # if "join_ido" in execute_msg:
    #     return handle_fee(exporter, txinfo, "join IDO")

    if "place_bid" in execute_msg:
        return handle_place_bid(exporter, elem, txinfo, index)

    if "settle" in execute_msg:
        return handle_settle(exporter, elem, txinfo, index)

    print("Knowhere!")
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_settle(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    events = elem["logs"][index]["events_by_type"]

    sent_amount = 0
    sent_currency = ""
    for a in events["transfer"]["amount"]:
        amount, currency = util_terra._amount(a)
        assert(sent_currency == "" or sent_currency == currency)
        sent_currency = currency
        sent_amount += amount

    contract = events["from_contract"]["contract_address"][-1]
    token_id = events["from_contract"]["token_id"][0]

    nft_currency = "{}_{}".format(contract, token_id)
    name = _nft_name(contract)

    row = make_nft_buy_tx(txinfo, sent_amount, sent_currency, nft_currency, name)
    exporter.ingest_row(row)

def handle_place_bid(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    bid = elem["logs"][index]["events_by_type"]["from_contract"]["auction_id"][0]
    bidder = elem["logs"][index]["events_by_type"]["execute_contract"]["sender"][0]

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    _, placed_bid = util_terra._transfers(elem, bidder, txid, index=index)
    amount, currency = util_terra._convert(*placed_bid[0])

    # Got overbid
    if len(transfers_in) == 1 and len(transfers_out) == 0:
        refund_amount, refund_currency = util_terra._convert(*transfers_in[0])
        row = make_nft_offer_refund(txinfo, refund_amount, refund_currency)
        row.comment += f" auction {bid} - overbid by {amount} {currency}"
        exporter.ingest_row(row)
        return

    assert(len(transfers_out) == 1)

    row = make_nft_offer_deposit(txinfo, amount, currency)
    row.comment += f" auction {bid}"
    exporter.ingest_row(row)