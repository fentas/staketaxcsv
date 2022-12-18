import logging
from terra import util_terra
from terra.execute_type import _execute_type

from terra.make_tx import (
    make_gov_stake_tx,
    make_gov_unstake_tx,
    make_swap_tx_terra,
)

from terra.constants import CUR_UST, MILLION

from common.make_tx import (
    make_just_fee_tx, 
    make_just_fee_txinfo,
    make_reward_tx,
    make_airdrop_tx,

    make_transfer_in_tx,
    make_transfer_out_tx,
)

from terra.col4 import (
    handle_governance,
    handle_simple,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)

from terra.data import contract_info

# static as dunno where to find online (api)
# price per token in UST
IDO = {
    'STARTERRA_LOOP_IDO_ROUND_1': 0.1,
    'STARTERRA_TERRALAND_IDO_VESTING': 0.09,
    'STARTERRA_ORION_IDO_VESTING': 0.15,
    'STARTERRA_STARTERRA_IDO_VESTING': 0.14,
    'STARTERRA_KUJIRA_IDO_VESTING': 0.18,
    'STARTERRA_ANGEL_IDO_VESTING': 0.05,
    'STARTERRA_SOLCHICKS_IDO_VESTING': 0.05,
    'STARTERRA_PLAYNITY_IDO_VESTING': 0.07,
    'STARTERRA_WIZARRE_IDO_VESTING': 0.00095,
    'STARTERRA_LUART_IDO_VESTING': 0.025,
    'STARTERRA_ROBO_IDO_VESTING': 0.012,
}

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    if "sign_to_faction" in execute_msg:
        return

    if "pay_for_ido" in execute_msg:
        return False
    if "register_address" in execute_msg:
        return handle_fee(exporter, txinfo, "register address for IDO")
    # pay ido just collects money from user vesting account
    # register_vesting_accounts registers amount for given ido
    if "join_ido" in execute_msg:
        return False
        return handle_join_ido(exporter, elem, txinfo)
    if "register_vesting_accounts" in execute_msg:
        handle_ido(exporter, elem, txinfo)
        return False
    if "register_airdrop_accounts" in execute_msg:
        return handle_airdrop(exporter, elem, txinfo)

    if "accept_terms_of_use" in execute_msg:
        return handle_fee(exporter, txinfo, "accept terms of use")
    if "sign_message" in execute_msg:
        return handle_fee(exporter, txinfo, "sign generic message")

    if "vote" in execute_msg:
        handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        return False

    if "unbond" in execute_msg:
        return handle_unstake(exporter, elem, txinfo, index)

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)
    
    if "submit_to_unbond" in execute_msg:
        return handle_submit_to_unbond(exporter, elem, txinfo, index)

    if "withdraw_deposit" in execute_msg:
        return handle_fee(exporter, txinfo, "withdraw")
        # return handle_withdraw_deposit(exporter, elem, txinfo, index)

    if "deposit" in execute_msg:
        return handle_fee(exporter, txinfo, "deposit")
        # return handle_deposit(exporter, elem, txinfo, index)

    print(f"StarTerra!")

    #print(elem)
    return True

def handle_deposit(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 0)
    assert(len(transfers_out) == 1)

    received_amount, received_currency = util_terra._convert(*transfers_out[0])
    row = make_transfer_out_tx(txinfo, received_amount, received_currency)
    exporter.ingest_row(row)

def handle_withdraw_deposit(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    received_amount, received_currency = util_terra._convert(*transfers_in[0])
    row = make_transfer_in_tx(txinfo, received_amount, received_currency)
    exporter.ingest_row(row)

def handle_join_ido(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    stt_contract = elem["tx"]["value"]["msg"][0]["value"]["contract"]
    init_msg = util_terra._query_wasm(stt_contract)

    # todo: make this work?
    print(stt_contract)
    print(init_msg)
    IDO[init_msg["ido_token"]] = float(init_msg["ido_token_price"]) / MILLION

def handle_ido(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    ido_contract = elem["tx"]["value"]["msg"][0]["value"]["contract"]
    init_msg = util_terra._query_wasm(ido_contract)
    received_currency = init_msg['starterra_token']

    info = contract_info(ido_contract)
    assert(info != None)
    print("-- current state:")
    print(info["id"])
    print(ido_contract)
    print(IDO)
    ido_price = 0
    if info["id"] in IDO:
        ido_price = IDO[info["id"]]
    elif received_currency in IDO:
        ido_price = IDO[received_currency]
    assert(ido_price != 0)

    for msg in elem["tx"]["value"]["msg"]:
        for va in msg["value"]["execute_msg"]["register_vesting_accounts"]["vesting_accounts"]:
            if va["address"] != wallet_address:
                continue

            token_amount = va["amount"]

            received_amount, received_currency = util_terra._convert(token_amount, received_currency)
            sent_amount = received_amount * ido_price
            sent_currency = CUR_UST

            row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency, empty_fee=True)
            exporter.ingest_row(row)
            return False

def handle_airdrop(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    contract = elem["tx"]["value"]["msg"][0]["value"]["contract"]
    init_msg = util_terra._query_wasm(contract)
    received_currency = init_msg["token_address"]

    for msg in elem["tx"]["value"]["msg"]:
        for ac in msg["value"]["execute_msg"]["register_airdrop_accounts"]["airdrop_accounts"]:
            if ac["address"] != wallet_address:
                continue

            token_amount = ac["amount"]

            amount, currency = util_terra._convert(token_amount, received_currency)

            row = make_airdrop_tx(txinfo, amount, currency, empty_fee=True)
            exporter.ingest_row(row)
            return False

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_submit_to_unbond(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    if len(transfers_out) == 0:
        # no unbond fee
        return

    amount, currency = util_terra._convert(*transfers_out[0])

    row = make_just_fee_tx(txinfo, amount, currency)
    row.comment += " - early unbond fee "
    exporter.ingest_row(row)

def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)

def handle_unstake(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get received amount
    log = elem["logs"][index]
    transfers_in, transfers_out = util_terra._transfers_log(log, wallet_address, from_contract=True)
    claim_amount, claim_currency = transfers_in[0]
    
    claim_currency = util_terra._lookup_address(claim_currency, txid)

    if 'burn' in log["events_by_type"]["from_contract"]:
        burn = util_terra._float_amount(log["events_by_type"]["from_contract"]["burn"][0], claim_currency)
        row = make_just_fee_tx(txinfo, burn, claim_currency)
        row.comment = " - [stt] burn fee for early claim"
        exporter.ingest_row(row)

    if len(transfers_out) == 1:
        fee_amount, fee_currency = transfers_out[0]
        row = make_just_fee_tx(txinfo, fee_amount, fee_currency)
        row.comment = " - [stt] general claim fee"
        exporter.ingest_row(row)

    row = make_gov_unstake_tx(txinfo, claim_amount, claim_currency)
    exporter.ingest_row(row)