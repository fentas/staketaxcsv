import logging
from terra import util_terra
from terra.execute_type import _execute_type

from .bond import (
    handle_bond, 
    handle_unbond, 
    handle_unbond_withdraw,
    handle_mint_collateral,
    handle_burn_collateral,
)
from .borrow import (
    handle_borrow,
    handle_deposit_collateral,
    handle_repay,
    handle_withdraw_collateral,
)
from .earn import (
    handle_anchor_earn_deposit, 
    handle_anchor_earn_withdraw,
)
from .liquidate import (
    handle_submit_bid,
    handle_retract_bid,
    handle_liquidate,
    handle_claim_liquidation,
)
from terra.col4 import (
    handle_reward_contract,
    handle_lp,
    handle_governance,
    handle_simple,
)
from terra.col5.handle import (
    _ingest_rows,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from terra.make_tx import (
    make_swap_tx_terra,
)
from common.make_tx import (
    make_just_fee_txinfo,
)

CONTRACTS = {
    "staking": "terra1897an2xux840p9lrh6py3ryankc6mspw49xse3",
}

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    if "lock_collateral" in execute_msg:
        return
    if "unlock_collateral" in execute_msg:
        return

    # Reward Transactions
    if "withdraw" in execute_msg:
        return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo, index)
    if "claim_rewards" in execute_msg:
        return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo, index)
    if "claim" in execute_msg:
        return handle_reward_contract.handle_airdrop(exporter, elem, txinfo, index)

    # Staking Transactions
    if "unbond" in execute_msg:
        return handle_lp.handle_lp_unstake(exporter, elem, txinfo, index)
    if "withdraw_voting_tokens" in execute_msg:
        return handle_governance.handle_governance_unstake(exporter, elem, txinfo, index)

    # Borrow Transactions
    if "borrow_stable" in execute_msg:
        return handle_borrow(exporter, elem, txinfo, index)
    if "repay_stable" in execute_msg:
        return handle_repay(exporter, elem, txinfo, index)
    
    if "withdraw_collateral" in execute_msg:
       return handle_withdraw_collateral(exporter, elem, txinfo, index)

    # Anchor Earn transactions
    if "deposit_stable" in execute_msg:
        return handle_anchor_earn_deposit(exporter, elem, txinfo, index)

    # Bond transactions
    if "bond" in execute_msg:
        return handle_bond(exporter, elem, txinfo, index)
    if "withdraw_unbonded" in execute_msg:
        return handle_unbond_withdraw(exporter, elem, txinfo, index)
    if "mint" in execute_msg:
        handle_mint_collateral(exporter, elem, txinfo, index)
        return False
    if "burn" in execute_msg:
        handle_burn_collateral(exporter, elem, txinfo, index)
        return False

    # Liquidations
    if "activate_bids" in execute_msg:
        return _ingest_rows(exporter, txinfo)
    if "submit_bid" in execute_msg:
        return handle_fee(exporter, txinfo, "submit bid")
        # return handle_submit_bid(exporter, elem, txinfo, index)
    if "retract_bid" in execute_msg:
        return handle_fee(exporter, txinfo, "retract bid")
        # return handle_retract_bid(exporter, elem, txinfo, index)
    if "liquidate" in execute_msg:
        return handle_liquidate(exporter, elem, txinfo, index)
    if "claim_liquidations" in execute_msg:
        return handle_claim_liquidation(exporter, elem, txinfo, index)

    # Governance
    if "cast_vote" in execute_msg:
        handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        return False

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        # Staking
        if "stake_voting_tokens" in msg:
            return handle_governance.handle_governance_stake(exporter, elem, txinfo, index)

        if "bond" in msg and send["contract"] == CONTRACTS["staking"]:
            return handle_lp.handle_lp_stake(exporter, elem, txinfo)

        # Borrow Transactions
        if "deposit_collateral" in msg:
            return handle_deposit_collateral(exporter, elem, txinfo, index)

        # Bond transactions
        if "unbond" in msg:
            return handle_unbond(exporter, elem, txinfo)

        # Earn transactions
        #if "deposit_stable" in msg:
        #    return handle_anchor_earn_deposit(exporter, elem, txinfo)
        if "redeem_stable" in msg:
            return handle_anchor_earn_withdraw(exporter, elem, txinfo, index)

        if "convert_anchor_to_wormhole" in msg:
            # return handle_fee(exporter, txinfo, "convert bETH to webETH")
            return handle_swap(exporter, elem, txinfo, index)

    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[anchor] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_swap(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    assert(len(transfers_out) == 1)

    offer_amount, offer_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    exporter.ingest_row(row)