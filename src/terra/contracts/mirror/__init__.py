import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)
from .borrow import (
    handle_deposit_borrow,
    handle_repay_withdraw,
)

from common.make_tx import (
    make_borrow_tx, 
    make_reward_tx,
    make_transfer_in_tx,
    make_transfer_out_tx,
)

from terra.col4.handle_governance import (
    handle_governance_unstake, 
    handle_governance_stake,
)

from terra.col4.handle_simple import (
    handle_simple,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from terra.col4.handle_lp import handle_lp_deposit, handle_lp_withdraw, handle_lp_stake, handle_lp_unstake

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    print(execute_msg)
    if "unlock_position_funds" in execute_msg:
        return handle_unlock(exporter, elem, txinfo, index)

    if "claim" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)

    if "cast_vote" in execute_msg:
        return handle_simple(exporter, txinfo, TX_TYPE_VOTE)

    if "auto_stake" in execute_msg:
        return handle_lp_deposit(exporter, elem, txinfo, index)

    if "unbond" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "withdraw_voting_tokens" in execute_msg:
        return handle_governance_unstake(exporter, elem, txinfo, index)

    if "withdraw" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)
    if "withdraw_voting_rewards" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)

    # wtf is this?
    if "transfer" in execute_msg:
        return handle_transfer(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]
        
        # Mirror Borrow Transactions
        if "open_position" in msg:
            return handle_deposit_borrow(exporter, elem, txinfo)
        if "burn" in msg:
            return handle_repay_withdraw(exporter, elem, txinfo)

        if "stake_voting_tokens" in msg:
            return handle_governance_stake(exporter, elem, txinfo, index)

    quit()
    print("Mirror!")
    return True

def handle_transfer(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    if len(transfers_in) > 0:
        amount, currency = util_terra._convert(*transfers_in[0])
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    if len(transfers_out) > 0:
        amount, currency = util_terra._convert(*transfers_out[0])
        row = make_transfer_out_tx(txinfo, amount, currency)
        exporter.ingest_row(row)

def handle_unlock(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_in) == 1 and len(transfers_out) == 0)

    borrow_amount, borrow_currency = util_terra._convert(*transfers_in[0])
    row = make_borrow_tx(txinfo, borrow_amount, borrow_currency)
    exporter.ingest_row(row)

def handle_claim(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)
