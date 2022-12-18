import logging
from terra import util_terra
from terra.make_tx import (
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_stake_tx,
    make_unstake_tx,
)
from terra.col4 import (
    handle_simple,
    handle_reward_contract,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from common.make_tx import (
    make_just_fee_tx,
    make_just_fee_txinfo,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    memo = elem["tx"]["value"]["memo"]

    # automated ticket buys
    if memo == "Automated worker Dogether!" or "Automated worker!":
        return False

    if "vote" in execute_msg:
        handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        return False

    if "unbond_stake" in execute_msg:
        return handle_unbond_stake(exporter, elem, txinfo, index)

    if "withdraw_stake" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "pool" in execute_msg:
        return handle_pool(exporter, elem, txinfo, index)

    if "un_pool" in execute_msg:
        return handle_fee(exporter, txinfo, "queue un-pool")

    if "claim_un_pool" in execute_msg:
        return handle_claim_un_pool(exporter, elem, txinfo, index)

    if "collect" in execute_msg:
        handle_reward_contract.handle_reward_contract(exporter, elem, txinfo)
        return False

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "bond_stake" in msg:
            return handle_lp_stake(exporter, elem, txinfo, index)

    print("LoTerra!")
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_unbond_stake(exporter, elem, txinfo, index):
    fee, currency = util_terra._convert(txinfo.fee, txinfo.fee_currency)
    row = make_just_fee_tx(txinfo, fee, currency)
    row.comment = " * trigger unbond period"
    exporter.ingest_row(row)

def handle_lp_stake(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])

    row = make_lp_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_lp_unstake(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_lp_unstake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_pool(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])

    row = make_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_claim_un_pool(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_unstake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)