from terra import util_terra
from terra.make_tx import (
    make_deposit_collateral_tx,
    make_lp_deposit_tx,
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_stake_tx,
    make_lp_withdraw_tx,
    make_withdraw_collateral_tx,
    make_swap_tx_terra,
)
from common.make_tx import (
    make_just_fee_txinfo,
    make_reward_tx,
)
from terra.col4.handle_lp import handle_lp_deposit, handle_lp_withdraw
from terra.col4 import (
    handle_reward_contract,
)
from terra.col4 import (
    handle_governance,
    handle_simple,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from terra.col4.handle_lp import _handle_lp_deposit, _handle_lp_withdraw

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    print(execute_msg)

    if "mint" in execute_msg:
        # spec mints rewards
        return

    if "update_stake" in execute_msg:
        return handle_fee(exporter, txinfo, "update stake lock period")

    if "poll_vote" in execute_msg:
        handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        return False

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)

    if "unbond" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "bond" in execute_msg:
        return handle_lp_deposit(exporter, elem, txinfo, index)

    if "zap_to_bond" in execute_msg:
        return handle_zap_to_bond(exporter, elem, txinfo, index)
        

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "bond" in msg:
            return handle_bond(exporter, elem, txinfo, index)

        if "zap_to_unbond" in msg:
            return handle_zap_to_unbond(exporter, elem, txinfo, index)

        if "stake_tokens" in msg:
            return handle_stake(exporter, elem, txinfo, index)

    quit()
    print('SPEC!')
    return True


def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    print(transfers_in)
    print(transfers_out)
    if len(transfers_in) == 0:
        return

    assert(len(transfers_out) == 0)

    amount, currency = util_terra._convert(*transfers_in[0])

    for transfer in transfers_in:
        amount, currency = util_terra._convert(*transfer)

        row = make_reward_tx(txinfo, amount, currency, txid)
        exporter.ingest_row(row)

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

# 1) lp unstake row happens usally in first message
# 2) lp withdraw collateral rows
# 3) swap row
def handle_zap_to_unbond(exporter, elem, txinfo, index):
    comment = " *zap out of strategy"
    from_contract = elem["logs"][index]["events_by_type"]["from_contract"]

    rows = []
    rows.extend(_handle_lp_withdraw(elem, txinfo, from_contract, index))
    rows.extend(_handle_swap(txinfo, from_contract))
    util_terra._ingest_rows(exporter, rows, comment)

def handle_zap_to_bond(exporter, elem, txinfo, index):
    comment = " *zap into strategy"
    from_contract = elem["logs"][index]["events_by_type"]["from_contract"]

    rows = []
    rows.extend(_handle_lp_deposit(txinfo, from_contract))
    rows.extend(_handle_swap(txinfo, from_contract))
    util_terra._ingest_rows(exporter, rows, comment)

def _handle_swap(txinfo, from_contract):
    txid = txinfo.txid

    # Handle swap
    swap_sent_currency = util_terra._asset_to_currency(from_contract["offer_asset"][0], txid)
    swap_sent_amount = util_terra._float_amount(from_contract["offer_amount"][0], swap_sent_currency)
    swap_received_currency = util_terra._asset_to_currency(from_contract['ask_asset'][0], txid)
    swap_received_amount = util_terra._float_amount(from_contract["return_amount"][0], swap_received_currency)

    # Make swap row
    row = make_swap_tx_terra(txinfo, swap_sent_amount, swap_sent_currency, swap_received_amount, swap_received_currency)
    return [row]

def handle_stake(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)

    amount, currency = util_terra._convert(*transfers_out[0])

    row = make_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_bond(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)
    amount, currency = util_terra._convert(*transfers_out[0])

    # Create _LP_UNSTAKE row
    row = make_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)

def handle_lp_unstake(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)
    lp_amount, lp_currency = transfers_in[0]
    lp_currency = util_terra._lookup_address(lp_currency, txid)
    lp_amount = util_terra._float_amount(lp_amount, lp_currency)

    # Create _LP_UNSTAKE row
    row = make_lp_unstake_tx(txinfo, lp_amount, lp_currency)
    exporter.ingest_row(row)