from terra import util_terra
from terra.make_tx import (
    make_liquidate_tx,
    make_submit_bid_tx,
    make_retract_bid_tx
)
from common.make_tx import make_repay_tx, make_swap_tx
from terra.constants import CUR_UST

# todo: somhow match bids with claim and retract ...
_bids = []

def handle_liquidate(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    from_contract = elem["logs"][index]["events_by_type"]["from_contract"]

    # Extract repay amount
    repay_amount_string = from_contract["repay_amount"][1]
    repay_currency_string = from_contract["stable_denom"][0]
    repay_amount, repay_currency = util_terra._amount(repay_amount_string + repay_currency_string)

    # Extract liquidated collateral
    collateral_amount_string = from_contract["collateral_amount"][0]
    collateral_currency_string = from_contract["collateral_token"][0]
    collateral_amount, collateral_currency = util_terra._amount(collateral_amount_string + collateral_currency_string)

    if wallet_address in from_contract["liquidator"]:
        row = make_liquidate_tx(txinfo, repay_amount, repay_currency, collateral_amount, collateral_currency)
        exporter.ingest_row(row)
    else:
        row = make_liquidate_tx(txinfo, collateral_amount, collateral_currency, repay_amount, repay_currency)
        exporter.ingest_row(row)
        row = make_repay_tx(txinfo, repay_amount, repay_currency)
        exporter.ingest_row(row)


def handle_submit_bid(exporter, elem, txinfo, index):
    # Extract bid amount
    transfer = elem["logs"][index]["events_by_type"]["transfer"]
    bid_string = transfer["amount"][0]
    bid_amount, bid_currency = util_terra._amount(bid_string)

    row = make_submit_bid_tx(txinfo, bid_amount, bid_currency)
    exporter.ingest_row(row)

    print("!_!")
    print(bid_amount)
    print(elem)
    _bids.append(bid_amount)


def handle_retract_bid(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet = txinfo.wallet_address

    # Extract bid amount
    transfers_in, _ = util_terra._transfers(elem, wallet, txid, index=index)
    bid_amount, bid_currency = transfers_in[0]
    row = make_retract_bid_tx(txinfo, bid_amount, bid_currency)

    # Extract fee, if any, paid by anchor market contract to fee collector
    row = util_terra._add_anchor_fees(elem, txid, row)
    exporter.ingest_row(row)

    if bid_amount in _bids: 
        print("!-!")
        print(bid_amount)
        print(elem)
        _bids.remove(bid_amount)
    else:
        print("AAAAAAAAAAAAAAAAAAA")
        print(txid)

# https://docs.anchorprotocol.com/smart-contracts/liquidations/liquidation-queue-contract#bid
# bidx_ids are not lookupable afterwards ...
def handle_claim_liquidation(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet = txinfo.wallet_address

    # Extract bid amount
    transfers_in, _ = util_terra._transfers(elem, wallet, txid, index=index)
    bid_amount, bid_currency = util_terra._convert(*transfers_in[0])

    msg = util_terra._execute_msg(elem, index)
    bids = msg["claim_liquidations"]["bids_idx"]

    # print("!o!")
    # print(bids)
    # print(_bids)
    #l = len(bids) if len(bids) >= len(_bids) else len(_bids)
    #sent_amount = sum(_bids.pop() for i in range(l))
    # sent_amount = _bids.pop() if len(_bids) > 0 else 0
    price = exporter.coinhall.price(bid_currency, txinfo.timestamp)
    assert("open" in price)
    sent_amount = bid_amount * price["open"]

    row = make_swap_tx(txinfo, sent_amount, CUR_UST, bid_amount, bid_currency, txid)
    exporter.ingest_row(row)