import logging
import importlib
from datetime import datetime

import terra.execute_type as ex
from common.ErrorCounter import ErrorCounter
from common.ExporterTypes import TX_TYPE_GOV, TX_TYPE_LOTA_UNKNOWN, TX_TYPE_VOTE
from common.make_tx import make_just_fee_tx
from common.TxInfo import TxInfo
from terra import util_terra
from terra.config_terra import localconfig
from terra.constants import CONTRACT_RANDOMEARTH, CONTRACTS_LOTA, EXCHANGE_TERRA_BLOCKCHAIN
from terra.handle_failed_tx import handle_failed_tx
from terra.handle_governance import handle_governance_reward, handle_governance_stake, handle_governance_unstake
from terra.handle_lp import (
    handle_lp_deposit,
    handle_lp_deposit_idx,
    handle_lp_long_farm,
    handle_lp_stake,
    handle_lp_stake_deposit_strategy,
    handle_lp_unstake,
    handle_lp_unstake_withdraw_from_strategy,
    handle_lp_withdraw,
    handle_lp_withdraw_idx,
)
from terra.handle_nft import (
    handle_accept_deposit,
    handle_add_to_deposit,
    handle_add_whitelist,
    handle_approve,
    handle_execute_order,
    handle_mint_nft,
    handle_purchase_nft,
    handle_reserve_nft,
    handle_send_nft,
    handle_transfer_nft,
    handle_withdraw,
)
from terra.handle_reward import handle_reward
from terra.handle_reward_contract import handle_airdrop, handle_reward_contract
from terra.handle_reward_pylon import handle_airdrop_pylon
from terra.handle_simple import handle_simple, handle_unknown, handle_unknown_detect_transfers
from terra.handle_swap import handle_execute_swap_operations, handle_swap, handle_swap_msgswap
from terra.handle_transfer import handle_transfer, handle_transfer_bridge_wormhole, handle_transfer_contract

import terra.contracts.unspecific as unspecific
from terra.data import contract_info

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

    # Failed transaction
    if "code" in elem:
        return handle_failed_tx(exporter, elem, txinfo)

    index = -1
    for msg in elem["tx"]["value"]["msg"]:
        index += 1

        # filter parts of tranaction
        msgtype = msg["type"]

        try:
            if msgtype == "bank/MsgSend":
                return handle_transfer(exporter, elem, txinfo, index)
            elif msgtype == "bank/MsgMultiSend":
                # https://fcd.terra.dev/v1/tx/2bcb9bea8f74b0692196f5438e346d5b1c11d4a2edb5a7ce0b3029e46455a691
                print("TODO multisend!")
                return
            elif msgtype in ["gov/MsgVote", "gov/MsgDeposit"]:
                return handle_simple(exporter, txinfo, TX_TYPE_GOV)
            elif msgtype == "market/MsgSwap":
                return handle_swap_msgswap(exporter, elem, txinfo)
            elif msgtype in ["staking/MsgDelegate", "distribution/MsgWithdrawDelegationReward",
                            "staking/MsgBeginRedelegate", "staking/MsgUndelegate"]:
                # LUNA staking reward
                return handle_reward(exporter, elem, txinfo, msgtype)
            elif msgtype == "wasm/MsgExecuteContract":
                # general info
                contract = msg["value"]["contract"]
                # decode message
                execute_msg = util_terra._execute_msg(elem, index)
                msg["value"]["execute_msg"] = execute_msg

                # skip increase allowance
                if "increase_allowance" in execute_msg:
                    continue

                # send specific currency to other contract
                if "send" in execute_msg and "contract" in execute_msg["send"]:
                    contract = execute_msg["send"]["contract"]
    
                # Handle contracts
                execute_type = None
                info = contract_info(contract)
                if info is not None:
                    protocol = info['protocol'].lower()
                    try:
                        # try to load protocol
                        c = importlib.import_module(f"terra.contracts.{protocol}")

                        # Custom handle transaction
                        execute_type = c.handle(exporter, elem, txinfo, index)

                        # If no execute type is returned there nothing to do anymore
                        if execute_type is None:
                            return

                    except ModuleNotFoundError:
                        logging.warn("Not supported protocol %s ...", protocol)
                        print(info)
                elif contract in unspecific.CONTRACTS:
                    execute_type = unspecific.handle(exporter, elem, txinfo, index)
                else:
                    logging.warn("Unknown protocol contract=%s txid=%s", contract, txid)
                    execute_type = ex._execute_type(elem, txinfo)

                # First check if we could figure out the process type
                if execute_type == ex.EXECUTE_TYPE_UNKNOWN:
                    logging.error("Exception when handling contract=%s txid=%s", contract, txid)
                    ErrorCounter.increment("exception", txid)
                    handle_unknown(exporter, txinfo)
                    return

                # General
                if execute_type in EXECUTE_TYPES_SIMPLE:
                    tx_type = EXECUTE_TYPES_SIMPLE[execute_type]
                    return handle_simple(exporter, txinfo, tx_type)
                elif execute_type == ex.EXECUTE_TYPE_CLAIM:
                    return handle_airdrop(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_TRANSFER:
                    # Currently handles transfer to/from shuttle bridge
                    return handle_transfer_contract(exporter, elem, txinfo)

                # nft transactions
                elif execute_type in (ex.EXECUTE_TYPE_ADD_WHITELIST,
                                    ex.EXECUTE_TYPE_ADD_MULTIPLE_USERS_TO_WHITE_LIST,
                                    ex.EXECUTE_TYPE_ADD_TO_WHITELIST):
                    return handle_add_whitelist(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_ADD_TO_DEPOSIT:
                    return handle_add_to_deposit(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_ACCEPT_DEPOSIT:
                    return handle_accept_deposit(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_RESERVE_NFT:
                    return handle_reserve_nft(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_MINT_NFT:
                    return handle_mint_nft(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_PURCHASE_NFT:
                    return handle_purchase_nft(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_EXECUTE_ORDER:
                    return handle_execute_order(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_TRANSFER_NFT:
                    return handle_transfer_nft(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_SEND_NFT:
                    return handle_send_nft(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_APPROVE:
                    return handle_approve(exporter, elem, txinfo)
                elif contract == CONTRACT_RANDOMEARTH:
                    execute_msgs_keys = util_terra._execute_msgs_keys(elem)

                    if execute_type == ex.EXECUTE_TYPE_WITHDRAW:
                        handle_withdraw(exporter, elem, txinfo)
                        if len(execute_msgs_keys) == 2 and execute_msgs_keys[1] == ex.EXECUTE_TYPE_TRANSFER_NFT:
                            handle_transfer_nft(exporter, elem, txinfo, 1)
                        return
                    elif ex.EXECUTE_TYPE_EXECUTE_ORDER in execute_msgs_keys:
                        return handle_execute_order(exporter, elem, txinfo)
                    else:
                        handle_unknown(exporter, txinfo)

                # Swaps
                elif execute_type == ex.EXECUTE_TYPE_SWAP:
                    return handle_swap(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS:
                    return handle_execute_swap_operations(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS_IN_MSG:
                    return handle_execute_swap_operations(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_ASSERT_LIMIT_ORDER:
                    return handle_swap_msgswap(exporter, elem, txinfo)

                # Governance staking
                elif execute_type == ex.EXECUTE_TYPE_STAKE_VOTING_TOKENS:
                    return handle_governance_stake(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_VOTING_TOKENS:
                    return handle_governance_unstake(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_VOTING_REWARDS:
                    return handle_governance_reward(exporter, elem, txinfo)


                # LP transactions
                elif execute_type == ex.EXECUTE_TYPE_PROVIDE_LIQUIDITY:
                    return handle_lp_deposit(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_LIQUIDITY:
                    return handle_lp_withdraw(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_BOND_IN_MSG:
                    return handle_lp_stake(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_DEPOSIT_STRATEGY_ID_IN_MSG:
                    return handle_lp_stake_deposit_strategy(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_UNBOND:
                    return handle_lp_unstake(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_FROM_STRATEGY:
                    return handle_lp_unstake_withdraw_from_strategy(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_AUTO_STAKE:
                    return handle_lp_long_farm(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_IDX:
                    return handle_lp_withdraw_idx(exporter, elem, txinfo)
                elif execute_type in [ex.EXECUTE_TYPE_DEPOSIT_IDX, ex.EXECUTE_TYPE_DEPOSIT_IDX_IN_MSG]:
                    return handle_lp_deposit_idx(exporter, elem, txinfo)

                # Contract reward transactions
                elif execute_type in (ex.EXECUTE_TYPE_CLAIM_REWARDS, ex.EXECUTE_TYPE_WITHDRAW):
                    return handle_reward_contract(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_AIRDROP:
                    return handle_airdrop_pylon(exporter, elem, txinfo)

                # Bridge transfers
                elif execute_type == ex.EXECUTE_TYPE_DEPOSIT_TOKENS:
                    # wormhole bridge: transfer out
                    return handle_transfer_bridge_wormhole(exporter, elem, txinfo)
                elif execute_type == ex.EXECUTE_TYPE_SUBMIT_VAA:
                    # wormhole bridge: transfer in
                    return handle_transfer_bridge_wormhole(exporter, elem, txinfo)

                else:
                    logging.error("Unknown execute_type for txid=%s", txid)
                    ErrorCounter.increment("unknown_execute_type", txid)
                    handle_unknown_detect_transfers(exporter, txinfo, elem)
            else:
                logging.error("Unknown msgtype for txid=%s", txid)
                ErrorCounter.increment("unknown_msgtype", txid)
                handle_unknown_detect_transfers(exporter, txinfo, elem)

        except NameError as e: # Exception 
            logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
            ErrorCounter.increment("exception", txid)
            handle_unknown(exporter, txinfo)

            if localconfig.debug:
                raise (e)
    


def _txinfo(exporter, elem, wallet_address):
    txid = elem["txhash"]
    logging.debug("process_tx() txid=%s", txid)

    timestamp = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency, more_fees = _get_fee(elem)
    url = "https://finder.terra.money/mainnet/tx/{}".format(txid)
    txinfo = TxInfo(txid, timestamp, fee, fee_currency, wallet_address, EXCHANGE_TERRA_BLOCKCHAIN, url)
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
    if len(amounts) == 0:
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
