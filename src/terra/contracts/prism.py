from terra import util_terra
from terra.make_tx import (
    make_lp_deposit_tx,
    make_lp_withdraw_tx,
    make_swap_tx_terra,
)
from common.make_tx import (
    make_reward_tx,
    make_just_fee_txinfo,
)
from terra.col4 import (
    handle_lp,
)
from common.make_tx import make_just_fee_tx

from common.ExporterTypes import (
    TX_TYPE_VOTE,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "activate_boost" in execute_msg:
        return handle_fee(exporter, txinfo, "activate AMPS boost")

    if "swap" in execute_msg:
        return handle_swap(exporter, elem, txinfo, index)

    if "provide_liquidity" in execute_msg:
        return handle_provide_lp(exporter, elem, txinfo, index)

    # todo:
    if "withdraw_tokens" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)

    if "bond_split" in execute_msg:
        return handle_bond_split(exporter, elem, txinfo, index)
    
    if "convert_and_claim_rewards" in execute_msg:
        return handle_convert_and_claim_rewards(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "swap" in msg:
            return handle_swap(exporter, elem, txinfo, index)
        if "withdraw" in msg:
            return handle_withdraw_lp(exporter, elem, txinfo, index)
        if "withdraw_liquidity" in msg:
            return handle_withdraw_lp(exporter, elem, txinfo, index)
        if "mint_xprism" in msg:
            return handle_mint_xprism(exporter, elem, txinfo, index)


    print(f"Prism!")
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_convert_and_claim_rewards(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    assert(len(transfers_in) >= 1)
    assert(len(transfers_out) == 0)

    amount = 0
    currency = ""

    # sum up
    for transfer in transfers_in:
        amount1, currency1 = util_terra._convert(*transfer)
        assert(currency == "" or currency == currency1)
        currency = currency1
        amount += amount1

    row = make_reward_tx(txinfo, amount, currency, txid)
    row.comment += " *convert rewards"
    exporter.ingest_row(row)

def handle_bond_split(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 2)
    assert(len(transfers_out) == 1)

    offer_amount, offer_currency = util_terra._convert(*transfers_out[0])
    received_amount1, received_currency1 = util_terra._convert(*transfers_in[0])
    received_amount2, received_currency2 = util_terra._convert(*transfers_in[1])

    row = make_swap_tx_terra(txinfo, offer_amount/2, offer_currency, received_amount1, received_currency1, txid)
    exporter.ingest_row(row)
    row = make_swap_tx_terra(txinfo, offer_amount/2, offer_currency, received_amount2, received_currency2, txid)
    exporter.ingest_row(row)

def handle_mint_xprism(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    assert(len(transfers_out) == 1)

    offer_amount, offer_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    row.comment += " *mint"
    exporter.ingest_row(row)

def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    row.comment += " *todo: is this a swap?"
    exporter.ingest_row(row)

def handle_withdraw_lp(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    assert(len(transfers_in) == 2)
    assert(len(transfers_out) == 1)
    amount1, currency1 = util_terra._convert(*transfers_in[0])
    amount2, currency2 = util_terra._convert(*transfers_in[1])
    lp_amount, lp_currency = util_terra._convert(*transfers_out[0])

    rows = []
    rows.append(make_lp_withdraw_tx(
        txinfo, lp_amount / 2, lp_currency, amount1, currency1, txid, empty_fee=False))
    rows.append(make_lp_withdraw_tx(
        txinfo, lp_amount / 2, lp_currency, amount2, currency2, txid, empty_fee=True))

    util_terra._ingest_rows(exporter, rows)

def handle_provide_lp(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)

    i = 0
    currency1 = util_terra._asset_to_currency(events["contract_address"][i+1], txid)
    amount1 = util_terra._float_amount(events["amount"][i], currency1)

    if len(transfers_out) == 1:
        amount2, currency2 = util_terra._convert(*transfers_out[0])
    else:
        # i = i + 1
        # currency2 = util_terra._asset_to_currency(events["contract_address"][i+1], txid)
        # amount2 = util_terra._float_amount(events["amount"][i], currency2)
        amount1, currency1 = util_terra._convert(*transfers_out[0])
        amount2, currency2 = util_terra._convert(*transfers_out[1])

    # i = i + 1
    # lp_currency = util_terra._asset_to_currency(events["contract_address"][i+1], txid)
    # lp_amount = util_terra._float_amount(events["amount"][i], lp_currency)
    lp_amount, lp_currency = util_terra._convert(*transfers_in[0])

    rows = []
    rows.append(make_lp_deposit_tx(
        txinfo, amount1, currency1, lp_amount / 2, lp_currency, txid))
    rows.append(make_lp_deposit_tx(
        txinfo, amount2, currency2, lp_amount / 2, lp_currency, txid))

    util_terra._ingest_rows(exporter, rows)

def handle_swap(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    offer_currency = util_terra._asset_to_currency(events["offer_asset"][0], txid)
    offer_amount = util_terra._float_amount(events["offer_amount"][0], offer_currency)

    received_currency = util_terra._asset_to_currency(events["contract_address"][-2], txid)
    fee_amount = util_terra._float_amount(events["protocol_fee_amount"][0], received_currency)
    received_amount = util_terra._float_amount(events["return_amount"][0], received_currency) + fee_amount

    row = make_swap_tx_terra(txinfo, offer_amount, offer_currency, received_amount, received_currency, txid)
    exporter.ingest_row(row)

    row = make_just_fee_tx(txinfo, fee_amount, received_currency)
    row.comment = " * protocol fee"
    exporter.ingest_row(row)