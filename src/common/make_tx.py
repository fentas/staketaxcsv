from common.Exporter import Row
from common.ExporterTypes import (
    TX_TYPE_AIRDROP,
    TX_TYPE_BORROW,
    TX_TYPE_INCOME,
    TX_TYPE_REPAY,
    TX_TYPE_SOL_TRANSFER_SELF,
    TX_TYPE_SPEND,
    TX_TYPE_STAKING,
    TX_TYPE_TRADE,
    TX_TYPE_TRANSFER,
    TX_TYPE_UNKNOWN,
    TX_TYPE_FEE,
    TX_TYPE_FEE_SETTLEMENT,
    TX_TYPE_LP_DEPOSIT,
    TX_TYPE_LP_WITHDRAW,
    TX_TYPE_FEE_BORROWING,
)
from settings_csv import DONATION_WALLETS

from terra.data import contract_info
from terra.util_terra import _convert

# just a workaround to make sure that only one time fees are applied
_TX_FEE = {}

def make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                 txid=None, empty_fee=False):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                             TX_TYPE_TRADE, txid, empty_fee)


def make_airdrop_tx(txinfo, reward_amount, reward_currency, txid=None, empty_fee=False):
    return _make_tx_received(txinfo, reward_amount, reward_currency, TX_TYPE_AIRDROP, txid, empty_fee=empty_fee)


def make_income_tx(txinfo, income_amount, income_currency, txid=None, empty_fee=False):
    return _make_tx_received(txinfo, income_amount, income_currency, TX_TYPE_INCOME, txid, empty_fee=empty_fee)


def make_reward_tx(txinfo, reward_amount, reward_currency, txid=None, empty_fee=False, z_index=0):
    """ Staking reward transaction """
    return _make_tx_received(txinfo, reward_amount, reward_currency, TX_TYPE_STAKING, txid, empty_fee, z_index=z_index)


def make_spend_tx(txinfo, sent_amount, sent_currency):
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_SPEND)


def make_just_fee_tx(txinfo, fee_amount, fee_currency, tx_type=TX_TYPE_FEE, empty_fee=True):
    return _make_tx_sent(txinfo, fee_amount, fee_currency, tx_type, empty_fee=empty_fee)

def make_just_fee_txinfo(txinfo, tx_type=TX_TYPE_FEE, empty_fee=True):
    fee_amount, fee_currency = _convert(txinfo.fee, txinfo.fee_currency)
    return _make_tx_sent(txinfo, fee_amount, fee_currency, tx_type, empty_fee=empty_fee)


def make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest_address=None):
    if dest_address and dest_address in DONATION_WALLETS:
        return make_spend_tx(txinfo, sent_amount, sent_currency)
    else:
        info = contract_info(dest_address)
        if info is not None and 'fees' in info:
            txinfo.comment += " - fees for " + info['protocol']
            return make_just_fee_tx(txinfo, sent_amount, sent_currency)
        else:
            return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_TRANSFER)


def make_transfer_in_tx(txinfo, received_amount, received_currency):
    # Adjust to no fees for transfer-in transactions
    txinfo.fee = ""
    txinfo.fee_currency = ""

    if DONATION_WALLETS and txinfo.wallet_address in DONATION_WALLETS:
        row = _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_INCOME)
        row.comment = "donation " + row.comment
        return row
    else:
        return _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_TRANSFER)


def make_transfer_self(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_SOL_TRANSFER_SELF)


def make_borrow_tx(txinfo, received_amount, received_currency, empty_fee=False, z_index=0):
    txinfo.comment = "borrow " + txinfo.comment
    return _make_tx_received(
        txinfo, received_amount, received_currency, TX_TYPE_BORROW, empty_fee=empty_fee, z_index=z_index)


def make_repay_tx(txinfo, sent_amount, sent_currency, z_index=0):
    txinfo.comment = "*repay " + txinfo.comment
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_REPAY, z_index=z_index)

def make_repay_borrow_fee_tx(txinfo, sent_amount, sent_currency, z_index=0):
    txinfo.comment = "*borrow fee " + txinfo.comment
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_FEE_BORROWING, z_index=z_index)

def make_simple_tx(txinfo, tx_type, z_index=0):
    fee_currency = txinfo.fee_currency if txinfo.fee else ""

    row = Row(
        timestamp=txinfo.timestamp,
        tx_type=tx_type,
        received_amount="",
        received_currency="",
        sent_amount="",
        sent_currency="",
        fee=txinfo.fee,
        fee_currency=fee_currency,
        exchange=txinfo.exchange,
        wallet_address=txinfo.wallet_address,
        txid=txinfo.txid,
        url=txinfo.url,
        z_index=z_index,
        comment=txinfo.comment
    )
    return row


def make_unknown_tx(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_UNKNOWN)


def make_unknown_tx_with_transfer(txinfo, sent_amount, sent_currency, received_amount,
                                  received_currency, empty_fee=False, z_index=0):
    return _make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_UNKNOWN,
        empty_fee=empty_fee, z_index=z_index
    )


def _make_tx_received(txinfo, received_amount, received_currency, tx_type, txid=None, empty_fee=False, z_index=0):
    txid = txid if txid else txinfo.txid

    if txid in _TX_FEE or empty_fee:
        fee = ""
    else:
        fee = txinfo.fee
        _TX_FEE[txid] = txinfo

    fee_currency = txinfo.fee_currency if fee else ""

    row = Row(
        timestamp=txinfo.timestamp,
        tx_type=tx_type,
        received_amount=received_amount,
        received_currency=received_currency,
        sent_amount="",
        sent_currency="",
        fee=fee,
        fee_currency=fee_currency,
        exchange=txinfo.exchange,
        wallet_address=txinfo.wallet_address,
        txid=txid,
        url=txinfo.url,
        z_index=z_index,
        comment=txinfo.comment
    )
    return row


def _make_tx_sent(txinfo, sent_amount, sent_currency, tx_type, empty_fee=False, z_index=0):
    txid = txinfo.txid

    if txid in _TX_FEE or empty_fee:
        fee = ""
    else:
        fee = txinfo.fee
        _TX_FEE[txid] = txinfo

    fee_currency = txinfo.fee_currency if fee else ""

    row = Row(
        timestamp=txinfo.timestamp,
        tx_type=tx_type,
        received_amount="",
        received_currency="",
        sent_amount=sent_amount,
        sent_currency=sent_currency,
        fee=fee,
        fee_currency=fee_currency,
        exchange=txinfo.exchange,
        wallet_address=txinfo.wallet_address,
        txid=txinfo.txid,
        url=txinfo.url,
        z_index=z_index,
        comment=txinfo.comment
    )
    return row


def _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency, tx_type,
                      txid=None, empty_fee=False, z_index=0):
    txid = txid if txid else txinfo.txid

    if txid in _TX_FEE or empty_fee:
        fee = ""
    else:
        fee = txinfo.fee
        _TX_FEE[txid] = txinfo

    fee_currency = txinfo.fee_currency if fee else ""

    row = Row(
        timestamp=txinfo.timestamp,
        tx_type=tx_type,
        received_amount=received_amount,
        received_currency=received_currency,
        sent_amount=sent_amount,
        sent_currency=sent_currency,
        fee=fee,
        fee_currency=fee_currency,
        exchange=txinfo.exchange,
        wallet_address=txinfo.wallet_address,
        txid=txid,
        url=txinfo.url,
        z_index=z_index,
        comment=txinfo.comment
    )
    return row
