import logging

from terra import util_terra
from terra.col4.handle_reward_contract import _handle_airdrop
from terra.col4.handle_lp import handle_lp_stake, handle_lp_unstake
from terra.col4.handle_governance import handle_governance_unstake, handle_governance_stake, _extract_amount
from terra.col4.handle_transfer import handle_transfer
from terra.col4 import (
    handle_reward_pylon,
)
from common.make_tx import make_transfer_in_tx, make_transfer_out_tx,  make_reward_tx

from terra.make_tx import (
    make_swap_tx_terra,
    make_lockup_tx,
    make_swap_tx_terra,
    make_unstake_tx,
)

# known contracts from protocol
CONTRACTS = [
    # 0: Airdrop address
    "terra1ud39n6c42hmtp2z0qmy8svsk7z3zmdkxzfwcf2",
    # 1: Pylon Pylon $TWD Pre-sale Swap Blunder
    "terra15fgzzle2em5m6w4ps6sm7htvm829pwhwe5t2nl",
    # 2: Governance
    "terra1xu8utj38xuw6mjwck4n97enmavlv852zkcvhgp",
    # 3: Staking,
    "terra19nek85kaqrvzlxygw20jhy08h3ryjf5kg4ep3l",
    # 4: Pylon PSI Swap
    "terra12k0p3qvfhy6j5e3ef8kzusy29lzwykk5d95kk5",
    # Pylon bPsiDP-24m Token / bPsiDP-24m
    "terra1zsaswh926ey8qa5x4vj93kzzlfnef0pstuca0y", 
]

def handle(exporter, elem, txinfo, index):
    contract = elem["tx"]["value"]["msg"][index]["value"]["contract"]

    # handle by contract
    if contract == CONTRACTS[0]:
        return _handle_airdrop(exporter, elem, txinfo, index)

    # This was returned later on so we make just an withdrawl
    #if contract == CONTRACTS[1]:
    #    txinfo.comment += " - this is returned later (failed swap)"
    #    return handle_transfer(exporter, elem, txinfo, index)

    execute_msg = util_terra._execute_msg(elem, index)

    # ignore whitelist (for swaps) requests
    if "configure" in execute_msg and "whitelist" in execute_msg["configure"]:
        return False

    if "airdrop" in execute_msg:
        if "allocate" in execute_msg["airdrop"]:
            # Just bulk register for airdrop
            return False

        handle_reward_pylon.handle_airdrop_pylon(exporter, elem, txinfo)
        return False

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index) # handle_governance_unstake(exporter, elem, txinfo, index)

    if "unbond" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    # put in UST in pool (one of two) UST -> PoolLP
    if "deposit" in execute_msg:
        return handle_pylon_deposit(exporter, elem, txinfo, index)

    # Pylon Pylon $TWD Pre-sale Swap Blunder Refund
    if "refund" in execute_msg:
        return handle_pylon_refund(exporter, elem, txinfo, index)

    if "claim" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        # Governance
        if "stake_voting_tokens" in msg:
            return handle_governance_stake(exporter, elem, txinfo, index)
        
        if "stake" in msg:
            return handle_governance_stake(exporter, elem, txinfo, index)

        # Bond transactions
        if "bond" in msg:
            return handle_lp_stake(exporter, elem, txinfo, index)

        # put in UST in pool (two of two) PoolLP -> Stake
        if "deposit" in msg:
            return handle_pylon_lockup(exporter, elem, txinfo, index)

        if "redeem" in msg:
            return handle_redeem(exporter, elem, txinfo, index)

        
    if "poll" in execute_msg:
        return True
    if "cast_vote" in execute_msg:
        return True
    if "withdraw_voting_tokens" in execute_msg:
        return True

    # Try generall col4 transaction
    logging.warn("[pylon] General transaction txid=%s msg=%s", elem["txhash"], execute_msg)
    return True

def handle_redeem(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    assert(len(transfers_out) == 1)

    received_amount, received_currency = util_terra._convert(*transfers_in[0])
    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency, txid=txid)
    exporter.ingest_row(row)

def handle_withdraw(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]
    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_unstake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_claim(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]
    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)

def handle_pylon_refund(exporter, elem, txinfo, index=0):
    """ Handles pylon refund """
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    log = elem["logs"][index]

    wallet_address = txinfo.wallet_address
    [[amount, currency]], _ = util_terra._transfers_log(log, wallet_address)

    txinfo.comment += " - this is a refund of failed $TWD allocation swap"
    row = make_transfer_in_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_pylon_deposit(exporter, elem, txinfo, index=0):
    """ Handles pylon pool deposit """
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    log = elem["logs"][index]

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    contract = log["events_by_type"]["from_contract"]["contract_address"][-1]

    assert(len(transfers_out) == 1)
    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    # PSI Swap
    if contract == CONTRACTS[4]:
        # Public sale price 0.01 UST / PSI
        received_amount = sent_amount * 0.01
        received_currency = "PSI"
        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency, txid=txid)

    # todo: check out price and coin allocated and make swap
    elif "allocated" in log["events_by_type"]["from_contract"]:
        row = make_transfer_out_tx(txinfo, sent_amount, sent_currency, contract)

    else:
        assert(len(transfers_in) == 1)
        print(transfers_in)
        received_amount, received_currency = util_terra._convert(*transfers_in[0])
        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)

    exporter.ingest_row(row)

def handle_pylon_lockup(exporter, elem, txinfo, index=0):
    """ Handles pylondp lockup """
    txid = txinfo.txid

    amount, currency = _extract_amount(elem, txid, "send", index)
    if amount and currency:
        row = make_lockup_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)