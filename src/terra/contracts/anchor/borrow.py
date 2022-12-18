from common.make_tx import (
    make_borrow_tx, 
    make_repay_tx,
    make_repay_borrow_fee_tx,
)
from terra import util_terra
from terra.constants import CUR_UST, MILLION
from terra.make_tx import (
    make_deposit_collateral_tx,
    make_withdraw_collateral_tx
)

from datetime import datetime
import sys
_this = sys.modules[__name__]
# todo: better way
_this.INTREST_RATE = 0.22
_this.BORROW = 141700
_this.CUMULATIVE_INTREST = 0
_this.LAST_DAY_CALCULATED = None

def handle_deposit_collateral(exporter, elem, txinfo, index=1):
    txid = txinfo.txid

    # 1st message: deposit_collateral
    # 2nd message: lock_collateral

    # Parse lock_collateral message
    wallet_address = txinfo.wallet_address
    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    
    assert (len(transfers_out) == 1)
    [amount, currency_address] = transfers_out[0]

    sent_currency = util_terra._lookup_address(currency_address, txid)
    sent_amount = util_terra._float_amount(amount, sent_currency)

    row = make_deposit_collateral_tx(txinfo, sent_amount, sent_currency)
    exporter.ingest_row(row)


def handle_withdraw_collateral(exporter, elem, txinfo, index=0):
    txid = txinfo.txid

    # 1st message: unlock_collateral
    # 2nd message: withdraw_collateral

    # Parse unlock_collateral execute_msg
    wallet_address = txinfo.wallet_address
    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    
    assert (len(transfers_in) == 1)
    [amount, currency_address] = transfers_in[0]

    received_currency = util_terra._lookup_address(currency_address, txid)
    received_amount = util_terra._float_amount(amount, received_currency)

    row = make_withdraw_collateral_tx(txinfo, received_amount, received_currency)
    exporter.ingest_row(row)


def handle_borrow(exporter, elem, txinfo, index):
    txid = txinfo.txid

    # Extract borrow amount
    wallet_address = txinfo.wallet_address
    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    borrow_amount, borrow_currency = transfers_in[0]
    row = make_borrow_tx(txinfo, borrow_amount, borrow_currency)

    _calculate_cumulative_intrest(elem)
    _this.BORROW += borrow_amount
    print(f">>> Borrowed: {_this.BORROW}")
    # Extract fee, if any, paid by anchor market contract to fee collector
    row = util_terra._add_anchor_fees(elem, txid, row)

    exporter.ingest_row(row)


def handle_repay(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    amount, currency = transfers_out[0]

    _calculate_cumulative_intrest(elem)
    _this.BORROW -= amount

    repay_fee_amount = _this.CUMULATIVE_INTREST if _this.CUMULATIVE_INTREST < amount else amount
    row = make_repay_borrow_fee_tx(txinfo, repay_fee_amount, currency)
    exporter.ingest_row(row)
    _this.CUMULATIVE_INTREST -= repay_fee_amount
    print(f">>> Repayed: {amount}")
    print(f">>> Payed intrest: {repay_fee_amount}")
    print(f">>> Open instrest to pay: {_this.CUMULATIVE_INTREST}")

    amount = amount - repay_fee_amount
    if amount > 0:
        row = make_repay_tx(txinfo, amount, currency)
        exporter.ingest_row(row)


def _calculate_cumulative_intrest(elem):
    now = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

    if _this.LAST_DAY_CALCULATED != None:
        since = (now - _this.LAST_DAY_CALCULATED).days
        if since < 1:
            return

        # Daily Compound Interest = [Start Amount * (1 + (Interest Rate / 365)) ^ (n * 365)] – Start Amount
        intrest = (_this.BORROW * pow(1 + (_this.INTREST_RATE / 365), since) - _this.BORROW)
        _this.CUMULATIVE_INTREST += intrest
        _this.BORROW += intrest
        print("> borrowed:")
        print(_this.BORROW)
        print("> days since last borrow")
        print(since)
        print("> intrest to pay:")
        print(_this.CUMULATIVE_INTREST)

    _this.LAST_DAY_CALCULATED = now
    print(f"$$$ TOTAL: {_this.BORROW + _this.CUMULATIVE_INTREST}")