import logging
from datetime import datetime

from cronos.config import localconfig
from cronos.constants import CUR_CRONOS, CURRENCIES, MILLION
from cronos.make_tx import make_cronos_reward_tx, make_transfer_receive_tx

# from common.TxInfo import TxInfo
from cronos.TxInfo import TxInfo
from common.ErrorCounter import ErrorCounter
from common.ExporterTypes import (
    TX_TYPE_STAKING_DELEGATE,
    TX_TYPE_STAKING_REDELEGATE,
    TX_TYPE_STAKING_UNDELEGATE,
    TX_TYPE_UNKNOWN,
    TX_TYPE_VOTE,
    TX_TYPE_FAILED,
)
from common.make_tx import make_simple_tx, make_transfer_out_tx
from settings_csv import TICKER_CRONOS


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)
    ErrorCounter.log(TICKER_CRONOS, wallet_address)


def process_tx(wallet_address, elem, exporter):
    txid = elem["hash"]

    timestamp = datetime.strptime(elem["blockTime"][:19], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    fee = _get_fee(elem)
    url = f"https://crypto.org/explorer/tx/{txid}"

    msg_types = _msg_types(elem)
    for i in range(0, len(msg_types)):
        msg_type = msg_types[i]

        # Make new unique TxInfo for each message
        cur_txid = f"{txid}-{i}"
        cur_fee = fee if i == 0 else ""
        txinfo = TxInfo(cur_txid, timestamp, cur_fee, wallet_address, url)

        try:
            #print(msg_type)
            _handle_tx(msg_type, exporter, txinfo, elem, txid, i)
        except Exception as e:
            logging.error("Exception when handling txid=%s, exception:%s", txid, str(e))
            handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)

            if localconfig.debug:
                raise (e)


def _handle_tx(msg_type, exporter, txinfo, elem, txid, i):
    if elem["success"] == False:
        handle_failed(exporter, txinfo)
    elif msg_type == "MsgSend":
        handle_transfer(exporter, txinfo, elem, i)
    elif msg_type in ("MsgWithdrawDelegatorReward", "MsgWithdrawDelegationReward"):
        handle_withdraw_reward(exporter, txinfo, elem, i)
    elif msg_type in ["MsgDelegate", "MsgUndelegate", "MsgBeginRedelegate"]:
        handle_del_reward(exporter, txinfo, elem, i, msg_type)
    elif msg_type == "MsgVote":
        handle_simple_tx(exporter, txinfo, TX_TYPE_VOTE)
    elif msg_type == "MsgUpdateClient":
        # IBC Update Client message: skip (comes with additional messages of interest)
        return
    elif msg_type == "MsgRecvPacket":
        try:
            handle_transfer_ibc_recv(exporter, txinfo, elem, i)
        except Exception:
            handle_unknown(exporter, txinfo)
    elif msg_type == "MsgTransfer":
        try:
            handle_transfer_ibc(exporter, txinfo, elem, i)
        except Exception:
            handle_unknown(exporter, txinfo)
    else:
        logging.error("Unknown msg_type=%s", msg_type)
        ErrorCounter.increment("unknown_msg_type_" + msg_type, txid)
        handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)


def handle_simple_tx(exporter, txinfo, tx_type):
    row = make_simple_tx(txinfo, tx_type)
    exporter.ingest_row(row)


def handle_unknown(exporter, txinfo):
    return handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)


def handle_failed(exporter, txinfo):
    return handle_simple_tx(exporter, txinfo, TX_TYPE_FAILED)

def handle_del_reward(exporter, txinfo, elem, msg_index, msg_type):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Use "withdraw_rewards" event if exists
    events = elem["logs"][msg_index]["events"]
    reward = _extract_withdraw_rewards(events, txid)
    if reward:
        row = make_cronos_reward_tx(txinfo, reward)
        exporter.ingest_row(row)
        return

    # Use transfer events secondarily
    transfers_in, _ = _extract_transfers(txinfo, events, wallet_address, txid)
    if transfers_in:
        for amount, currency, _, _ in transfers_in:
            row = make_cronos_reward_tx(txinfo, amount)
            exporter.ingest_row(row)
        return

    # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
    if msg_type == "MsgDelegate":
        handle_simple_tx(exporter, txinfo, TX_TYPE_STAKING_DELEGATE)
    elif msg_type == "MsgUndelegate":
        handle_simple_tx(exporter, txinfo, TX_TYPE_STAKING_UNDELEGATE)
    elif msg_type == "MsgBeginRedelegate":
        handle_simple_tx(exporter, txinfo, TX_TYPE_STAKING_REDELEGATE)


def handle_transfer_ibc(exporter, txinfo, elem, msg_index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    events = elem["logs"][msg_index]["events"]
    transfers_in, transfers_out = _extract_transfers(txinfo, events, wallet_address, txid)

    _handle_transfers(exporter, txinfo, transfers_in, transfers_out)


def handle_transfer_ibc_recv(exporter, txinfo, elem, msg_index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][msg_index]["events"]
    transfers_in, transfers_out = _extract_transfers(txinfo, events, wallet_address, txid)

    _handle_transfers(exporter, txinfo, transfers_in, transfers_out)


def handle_transfer(exporter, txinfo, elem, msg_index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    events = elem["logs"][msg_index]["events"]
    transfers_in, transfers_out = _extract_transfers(txinfo, events, wallet_address, txid)

    _handle_transfers(exporter, txinfo, transfers_in, transfers_out)


def _handle_transfers(exporter, txinfo, transfers_in, transfers_out):
    for amount, currency, sender, recipient in transfers_in:
        row = make_transfer_receive_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    for amount, currency, sender, recipient in transfers_out:
        row = make_transfer_out_tx(txinfo, amount, currency, recipient)
        exporter.ingest_row(row)


def handle_withdraw_reward(exporter, txinfo, elem, msg_index):
    txid = txinfo.txid

    events = elem["logs"][msg_index]["events"]
    reward = _extract_withdraw_rewards(events, txid)

    if reward:
        row = make_cronos_reward_tx(txinfo, reward)
        exporter.ingest_row(row)


def _extract_transfers(txinfo, events, wallet_address, txid):
    transfers_in = []
    transfers_out = []

    for event in events:
        #print(txinfo.txid)
        #print(event["type"])
        #print(event["attributes"])
        if event["type"] == "transfer":
            attributes = event["attributes"]
            for i in range(0, len(attributes), 3):
                recipient = attributes[i]["value"]
                sender = attributes[i + 1]["value"]
                amount_string = attributes[i + 2]["value"]

                if recipient == wallet_address:
                    amount, currency = _amount(amount_string)
                    transfers_in.append([amount, currency, sender, recipient])
                elif sender == wallet_address:
                    amount, currency = _amount(amount_string)
                    transfers_out.append([amount, currency, sender, recipient])

    return transfers_in, transfers_out


def _extract_withdraw_rewards(events, txid):
    for event in events:
        if event["type"] == "withdraw_rewards":
            attributes = event["attributes"]
            for kv in attributes:
                if kv["key"] == "amount":
                    if "value" in kv:
                        amount_string = kv["value"]
                        return _cronos(amount_string)
                    else:
                        # Missing value means reward of zero (as opposed to can't find)
                        return 0

    return None


def _cronos(basecro):
    """
    Example: '5340003basecro' -> 5.340003
    """
    amount, currency = _amount(basecro)
    assert currency == CUR_CRONOS
    return amount


def _amount(amount_string):
    """
    Example: '5340003basecro' -> 5.340003, CRO
    """
    if amount_string == "":
        return 0, None

    if "ibc" in amount_string:
        amount, address = amount_string.split("ibc/", 1)
        ibc_address = "ibc/{}".format(address)
        currency = CURRENCIES.get(ibc_address, ibc_address)
        amount = float(amount) / MILLION
        return amount, currency

    amount, currency = amount_string.split("base", 1)
    amount = float(amount) / MILLION
    currency = currency.upper()

    return amount, currency


def _get_fee(elem):
    amount_list = elem["fee"]
    if len(amount_list) == 0:
        return 0

    denom = amount_list[0]["denom"]
    amount_string = amount_list[0]["amount"]
    if denom != "basecro":
        raise Exception(f"Unexpected denom. denom={denom}")
    fee = float(amount_string) / MILLION
    return fee


def _msg_types(elem):
    """Returns list of @type values found in tx.body.messages"""
    return [msg["type"] for msg in elem["messages"]]