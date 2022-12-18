from terra import util_terra
from terra.col4 import (
    handle_governance,
)
from common.make_tx import (
    make_just_fee_txinfo,
    make_reward_tx,
)
from terra.col4.handle_lp import handle_lp_stake, handle_lp_unstake
from terra.make_tx import (
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_swap_tx_terra,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    # if "stake" in execute_msg:
    #     # return handle_stake(exporter, elem, txinfo, index)
    #     return handle_governance.handle_governance_stake(exporter, elem, txinfo, index)

    if "join_ido" in execute_msg:
        return handle_fee(exporter, txinfo, "join IDO")

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        # Staking
        if "stake" in msg:
            return handle_governance.handle_governance_stake(exporter, elem, txinfo, index)

        if "unstake_and_claim" in msg:
            return handle_unstake_and_claim(exporter, elem, txinfo, index)

        if "swap" in msg:
            return handle_swap(exporter, elem, txinfo, index)

    print(f"Loop!")
    return True

def handle_swap(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1 and len(transfers_out) == 1)

    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])
    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)

def handle_unstake_and_claim(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) >= 2)

    for t in transfers_in:
        amount, currency = util_terra._convert(*t)

        if currency.startswith("LP_"):
            row = make_lp_unstake_tx(txinfo, amount, currency)
            exporter.ingest_row(row)
        else:
            row = make_reward_tx(txinfo, amount, currency, txid)
            exporter.ingest_row(row)


def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)