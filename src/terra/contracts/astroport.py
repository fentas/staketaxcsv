import logging
from terra import util_terra

from terra.col5.contracts.config import CONTRACTS
from terra.constants import CUR_ASTRO, MILLION
from terra.make_tx import (
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_lp_deposit_tx,
    make_lp_withdraw_tx,
    make_stake_tx,
    make_swap_tx_terra,
)
from common.make_tx import (
    make_reward_tx,
    make_airdrop_tx,
    make_just_fee_txinfo,
    make_transfer_out_tx,
    make_transfer_in_tx,
)
from terra.col4.handle_lp import handle_lp_stake, handle_lp_unstake

import sys
this = sys.modules[__name__]
this.COLLECT = 0
this.COLLECT2 = 0
# todo find generic way
this.DEPOSIT_AUCTION = {
    'ust': 0,
    'astro': 0
}
this.LP_ASTRO_UST_AMOUNT = 80000

CONTRACT_ASTROPORT_AIRDROP = "terra1dpe2aqykm2vnakcz4vgpha0agxnlkjvgfahhk7"

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    txid = txinfo.txid
    contract = txinfo.msgs[index].contract

    if "claim" in execute_msg and contract == CONTRACT_ASTROPORT_AIRDROP:
        return handle_airdrop_claim(exporter, elem, txinfo, index)

    print(execute_msg)
    if "deposit_ust" in execute_msg:
        return handle_deposit_bootstrap_ust(exporter, elem, txinfo, index)
    if "delegate_astro_to_auction" in execute_msg:
        return handle_deposit_bootstrap_astro(exporter, elem, txinfo, index)
    if "delegate_astro_to_bootstrap_auction" in execute_msg:
        return handle_deposit_bootstrap_astro(exporter, elem, txinfo, index)
    if "claim_rewards" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)

    if "withdraw_from_lockup" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "provide_liquidity" in execute_msg:
        return handle_provide_lp(exporter, elem, txinfo, index)

    if "claim_rewards_and_optionally_unlock" in execute_msg:
        handle_bootstrap_lp(exporter, elem, txinfo, index)
        return handle_withdraw(exporter, elem, txinfo, index)

    if "swap" in execute_msg:
        return handle_swap(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        if "deposit" in msg:
            return handle_deposit(exporter, elem, txinfo, index)

        if "increase_lockup" in msg:
            return handle_fee(exporter, txinfo, "increase lockup")

        if "withdraw_liquidity" in msg:
            return handle_withdraw_lp(exporter, elem, txinfo, index)

        if "swap" in msg:
            return handle_swap(exporter, elem, txinfo, index)


    print("Astroport!")
    quit()
    return True

def handle_bootstrap_lp(exporter, elem, txinfo, index):
    if this.LP_ASTRO_UST_AMOUNT == 0:
        return

    txid = txinfo.txid
    lp_amount = this.LP_ASTRO_UST_AMOUNT
    lp_currency = "LP_ASTRO_UST"

    amount1 = this.DEPOSIT_AUCTION['ust']
    currency1 = 'UST'
    amount2 = this.DEPOSIT_AUCTION['astro']
    currency2 = 'ASTRO'

    rows = []
    rows.append(make_lp_deposit_tx(
        txinfo, amount1, currency1, lp_amount / 2, lp_currency, txid))
    rows.append(make_lp_deposit_tx(
        txinfo, amount2, currency2, lp_amount / 2, lp_currency, txid))
    util_terra._ingest_rows(exporter, rows)

    this.LP_ASTRO_UST_AMOUNT = 0

def handle_deposit_bootstrap_ust(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 0 and len(transfers_out) == 1)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    this.DEPOSIT_AUCTION['ust'] += sent_amount
    print(f"++ {this.DEPOSIT_AUCTION['ust']}")

def handle_deposit_bootstrap_astro(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    execute_msg = util_terra._execute_msg(elem, index)

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print("~astro handle_deposit_auction")
    print(transfers_in)
    print(transfers_out)

    if "delegate_astro_to_auction" in execute_msg:
        amount = float(execute_msg["delegate_astro_to_auction"]["amount"]) / MILLION
        currency = "ASTRO"
    elif "delegate_astro_to_bootstrap_auction" in execute_msg:
        amount = float(execute_msg["delegate_astro_to_bootstrap_auction"]["amount_to_delegate"]) / MILLION
        currency = "ASTRO"
    else:
        amount, currency = util_terra._convert(*transfers_out[0])
    # row = make_transfer_out_tx(txinfo, amount, currency)
    # exporter.ingest_row(row)
    assert(currency == "ASTRO")
    this.DEPOSIT_AUCTION['astro'] += amount

def handle_swap(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1 and len(transfers_out) == 1)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_deposit(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print("~astro handle_deposit")
    print(transfers_in)
    print(transfers_out)

    # This was bootstraping event
    # LP' staking
    if len(transfers_out) == 1:
        amount, currency = util_terra._convert(*transfers_out[0])
        row = make_lp_stake_tx(txinfo, amount, currency)
        exporter.ingest_row(row)

        if currency == 'LP_ASTRO_UST':
            this.COLLECT2 += amount
            print(f">>2 LP_ASTRO_UST: {this.COLLECT2}")

    if len(transfers_in) > 0:
        for transfer in transfers_in:
            amount, currency = util_terra._convert(*transfer)

            row = make_reward_tx(txinfo, amount, currency, txid)
            exporter.ingest_row(row)


def handle_provide_lp(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 2)

    rows = []
    if len(transfers_in) == 1:
        lp_amount, lp_currency = util_terra._convert(*transfers_in[0])
    else:
        from_contract = elem["logs"][index]["events_by_type"]["from_contract"]
        i_mint = from_contract["action"].index("mint")
        lp_currency = from_contract["contract_address"][i_mint]
        lp_amount = from_contract["amount"][i_mint]
        lp_amount, lp_currency = util_terra._convert(lp_amount, lp_currency)

        rows.append(make_lp_stake_tx(txinfo, lp_amount, lp_currency))

    amount1, currency1 = util_terra._convert(*transfers_out[0])
    amount2, currency2 = util_terra._convert(*transfers_out[1])

    rows.append(make_lp_deposit_tx(
        txinfo, amount2, currency2, lp_amount / 2, lp_currency, txid))
    rows.append(make_lp_deposit_tx(
        txinfo, amount1, currency1, lp_amount / 2, lp_currency, txid))
    rows.reverse()
    util_terra._ingest_rows(exporter, rows)
    


def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 0)
    assert(len(transfers_in) >= 1)

    for transfer in transfers_in:
        amount, currency = util_terra._convert(*transfer)

        if currency.startswith('LP_'):
            row = make_lp_unstake_tx(txinfo, amount, currency)
        else:
            row = make_reward_tx(txinfo, amount, currency, txid)
        exporter.ingest_row(row)

def handle_withdraw_lp(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_in) == 2)
    assert(len(transfers_out) == 1)
    amount1, currency1 = util_terra._convert(*transfers_in[0])
    amount2, currency2 = util_terra._convert(*transfers_in[1])
    lp_amount, lp_currency = util_terra._convert(*transfers_out[0])

    if lp_currency == 'LP_ASTRO_UST':
        this.COLLECT += lp_amount
        print(f">> LP_ASTRO_UST: {this.COLLECT}")

    exporter.ingest_row(make_lp_withdraw_tx(
        txinfo, lp_amount / 2, lp_currency, amount1, currency1, txid, empty_fee=False))
    exporter.ingest_row(make_lp_withdraw_tx(
        txinfo, lp_amount / 2, lp_currency, amount2, currency2, txid, empty_fee=True))

def handle_claim(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 0)
    assert(len(transfers_in) >= 1)

    for transfer in transfers_in:
        amount, currency = util_terra._convert(*transfer)

        if currency == "LP_ASTRO_UST":
            row = make_lp_unstake_tx(txinfo, amount, currency)
            exporter.ingest_row(row)
            continue

        row = make_reward_tx(txinfo, amount, currency, txid)
        exporter.ingest_row(row)

def handle_airdrop_claim(exporter, elem, txinfo, index):
    for action in txinfo.msgs[index].actions:
        if action["action"] == "Airdrop::ExecuteMsg::Claim":
            amount_string = action["airdrop"]
            currency = CUR_ASTRO
            amount = util_terra._float_amount(amount_string, currency)

            row = make_airdrop_tx(txinfo, amount, currency)
            exporter.ingest_row(row)
            return