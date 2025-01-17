import logging
import importlib
from datetime import datetime
from dateutil import tz
import pytz

import terra.execute_type as ex
from common.ErrorCounter import ErrorCounter
from common.ExporterTypes import TX_TYPE_GOV, TX_TYPE_LOTA_UNKNOWN, TX_TYPE_VOTE
from common.make_tx import make_just_fee_tx
from terra.TxInfoTerra import TxInfoTerra, MsgInfo
from terra import util_terra
from terra.config_terra import localconfig

import terra.contracts.unspecific as unspecific
from terra.data import contract_info

from terra.col4.handle_failed_tx import handle_failed_tx
from terra.col4.handle_simple import handle_simple, handle_unknown, handle_unknown_detect_transfers
from terra.col4.handle_swap import handle_swap_msgswap
from terra.col4.handle_reward import handle_reward
from terra.col4.handle_transfer import handle_transfer, handle_multi_transfer, handle_ibc_transfer
import terra.col4.handle
import terra.col5.handle

from terra.data import named_address
import common.Exporter as exp


# execute_type -> tx_type mapping for generic transactions with no tax details
EXECUTE_TYPES_SIMPLE = {
    ex.EXECUTE_TYPE_CAST_VOTE: TX_TYPE_VOTE,
    ex.EXECUTE_TYPE_REGISTER: TX_TYPE_LOTA_UNKNOWN,
}


def process_txs(wallet_address, elems, exporter, progress):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)

        if i % 50 == 0:
            progress.report(i + 1, "Processed {} of {} transactions".format(i + 1, len(elems)))


def process_tx(wallet_address, elem, exporter):
    txid = elem["txhash"]
    print(txid)
    txinfo = _txinfo(exporter, elem, wallet_address)
    print(f"---- {txinfo.timestamp}")

    # Failed transaction
    if "code" in elem:
        return handle_failed_tx(exporter, elem, txinfo)

    # Single action transactions
    # goes through logs (all transactsions)
    # so if processed multiple times it would duplicate transactions
    msgtype = elem["tx"]["value"]["msg"][0]["type"]

    index = -1
    for msg in elem["tx"]["value"]["msg"]:
        index += 1

        # filter parts of tranaction
        msgtype = msg["type"]

        # multi send goes through all logs
        # so it will be executed only once
        if msgtype == "ibc/MsgAcknowledgement":
            continue

        if msgtype == "bank/MsgMultiSend":
            handle_multi_transfer(exporter, elem, txinfo)
            return

        if msgtype == "cosmos-sdk/MsgTransfer":
            handle_ibc_transfer(exporter, elem, txinfo, index)
            continue
        if msgtype == "ibc/MsgUpdateClient":
            handle_ibc_transfer(exporter, elem, txinfo, index)
            continue
        if msgtype == "ibc/MsgRecvPacket":
            handle_ibc_transfer(exporter, elem, txinfo, index)
            continue
        # LUNA staking reward
        if msgtype in ["staking/MsgDelegate", "distribution/MsgWithdrawDelegationReward",
                        "staking/MsgBeginRedelegate", "staking/MsgUndelegate"]:
            handle_reward(exporter, elem, txinfo, msgtype, index)
            continue

        if msgtype == "market/MsgSwap":
            handle_swap_msgswap(exporter, elem, txinfo, index)
            continue
        if msgtype == "bank/MsgSend":
            handle_transfer(exporter, elem, txinfo, index)
            continue
        if msgtype in ["gov/MsgVote", "gov/MsgDeposit", "gov/MsgSubmitProposal"]:
            handle_simple(exporter, txinfo, TX_TYPE_GOV, index)
            continue

        # try:

        if msgtype == "wasm/MsgExecuteContract":
            # upstream contracts handling
            if terra.col5.handle.can_handle(exporter, elem, txinfo):
                # THIS SHOULD BE FIRST CHOICE TO ADD NEW HANDLERS
                terra.col5.handle.handle(exporter, elem, txinfo)
                logging.debug("Used col5 handler")
                return
        
            # general info
            contract = msg["value"]["contract"]
            # decode message
            execute_msg = util_terra._execute_msg(elem, index)
            msg["value"]["execute_msg"] = execute_msg

            # ignore list
            # maybe add later on generlized
            # nft collection whitelistings...
            if "add_to_list" in execute_msg:
                return

            # skip increase allowance
            if "increase_allowance" in execute_msg:
                continue

            # send specific currency to other contract
            if "send" in execute_msg and "contract" in execute_msg["send"]:
                contract = execute_msg["send"]["contract"]


            # Handle contracts
            execute_type = None
            info = contract_info(contract)
            print("!!!!!!!!!!!!!!")
            print(contract)
            print(info)
            if info is not None:
                protocol = info['protocol'].lower().replace(" ", "_")
                try:
                    # try to load protocol
                    c = importlib.import_module(f"terra.contracts.{protocol}")

                    # Custom handle transaction
                    exp.COMMENT_PROTOCOL = f"{info['protocol']} - {info['name']}"
                    execute_type = c.handle(exporter, elem, txinfo, index)
                    exp.COMMENT_PROTOCOL = ""

                    # If no execute type is returned there nothing to do anymore
                    if execute_type is None:
                        continue
                    if execute_type is False:
                        break

                except ModuleNotFoundError:
                    logging.warn("Not supported protocol %s ...", protocol)
                    print(info)
            elif contract in unspecific.CONTRACTS:
                execute_type = unspecific.handle(exporter, elem, txinfo, index)
                return
            else:
                logging.warn("Unknown protocol contract=%s txid=%s", contract, txid)
                execute_type = ex._execute_type(elem, txinfo)
                quit()

            # First check if we could figure out the process type
            if execute_type == ex.EXECUTE_TYPE_UNKNOWN:
                logging.error("Exception when handling contract=%s txid=%s", contract, txid)
                ErrorCounter.increment("exception", txid)
                handle_unknown(exporter, txinfo)
                return
            
            # Legacy handlers
            try:
                c = terra.col4.handle.handle_once(exporter, elem, txinfo, index)
                logging.debug("Used col4 handler")
                if c is False:
                    return
                else:
                    continue
            except NameError as e:
                logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
                ErrorCounter.increment("exception", txid)
                handle_unknown(exporter, txinfo)
        else:
            logging.error("Unknown msgtype for txid=%s msgtype=%s", txid, msgtype)
            ErrorCounter.increment("unknown_msgtype", txid)
            handle_unknown_detect_transfers(exporter, txinfo, elem, index)

        # except NameError as e: # Exception 
        #     logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
        #     ErrorCounter.increment("exception", txid)
        #     handle_unknown(exporter, txinfo)

        #     if localconfig.debug:
        #         raise (e)
    

    return txinfo


def _txinfo(exporter, elem, wallet_address):
    txid = elem["txhash"]
    timestamp = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").astimezone(tz = pytz.timezone('Europe/Berlin')).strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency, more_fees = _get_fee(elem)
    msgs = _msgs(elem, wallet_address)
    txinfo = TxInfoTerra(txid, timestamp, fee, fee_currency, wallet_address, msgs)
    msgtype = _get_first_msgtype(elem)

    # Handle transaction with multi-currency fee (treat as "spend" transactions)
    if more_fees:
        if msgtype == "bank/MsgSend" and elem["tx"]["value"]["msg"][0]["value"]["to_address"] == wallet_address:
            # This is a inbound transfer.  No fees
            pass
        else:
            for cur_fee, cur_currency in more_fees:
                row = make_just_fee_tx(txinfo, cur_fee, cur_currency)
                row.comment = "multicurrency fee"
                exporter.ingest_row(row)

    return txinfo


def _get_fee(elem):
    amounts = elem["tx"]["value"]["fee"]["amount"]

    # Handle special case for old transaction (16421CD60E56DA4F859088B7CA87BCF05A3B3C3F56CD4C0B2528EE0A797CC22D)
    if amounts is None or len(amounts) == 0:
        return 0, "", []

    # Parse fee element
    denom = amounts[0]["denom"]
    amount_string = amounts[0]["amount"]
    currency = util_terra._denom_to_currency(denom)
    fee = util_terra._float_amount(amount_string, currency)

    # Parse for tax info, add to fee if exists
    log = elem["logs"][0].get("log") if elem.get("logs") else None
    if log:
        tax_amount_string = log.get("tax", None)
        if tax_amount_string:
            tax_amount, tax_currency = util_terra._amount(tax_amount_string)
            if tax_currency == currency:
                fee += tax_amount

    if len(amounts) == 1:
        # "normal" single fee

        # Special case for old col-3 transaction 7F3F1FA8AC89824B64715FEEE057273A873F240CA9A50BC4A87EEF4EE9813905
        if fee == 0:
            return 0, "", []

        return fee, currency, []
    else:
        # multi-currency fee
        more_fees = []
        for info in amounts[1:]:
            cur_denom = info["denom"]
            cur_amount_string = info["amount"]
            cur_currency = util_terra._denom_to_currency(cur_denom)
            cur_fee = util_terra._float_amount(cur_amount_string, cur_currency)

            more_fees.append((cur_fee, cur_currency))
        return fee, currency, more_fees


def _get_first_msgtype(elem):
    """Returns type identifier for this transaction"""
    return elem["tx"]["value"]["msg"][0]["type"]


def _msgs(elem, wallet_address):
    if "logs" not in elem:
        return []

    out = []
    for i in range(len(elem["logs"])):
        msg_type = elem["tx"]["value"]["msg"][i]["type"]
        log = elem["logs"][i]

        if msg_type == "wasm/MsgExecuteContract":
            execute_msg = util_terra._execute_msg(elem, i)
            transfers = util_terra._transfers_log(log, wallet_address)
            actions = _actions(log)
            contract = util_terra._contract(elem, i)
        else:
            execute_msg = None
            transfers = [[], []]
            actions = []
            contract = None

        msginfo = MsgInfo(i, execute_msg, transfers, log, actions, contract)
        out.append(msginfo)

    return out


def _actions(log):
    events = log["events"]
    for event in events:
        attributes, event_type = event["attributes"], event["type"]

        if event_type == "wasm":
            actions = []
            action = {}

            for kv in attributes:
                k, v = kv["key"], kv["value"]

                if k == "contract_address":
                    # reached beginning of next action

                    # add previous action to list
                    if len(action):
                        actions.append(action)

                    # start new action
                    action = {}
                    action["contract_address"] = v
                else:
                    action[k] = v

            if len(action):
                actions.append(action)
            return actions

    return []
