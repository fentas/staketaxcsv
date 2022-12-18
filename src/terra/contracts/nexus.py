from terra import util_terra
from common.make_tx import (
    make_reward_tx,
)
from terra.make_tx import (
    make_swap_tx_terra,
    make_stake_tx,
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

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "claim" in execute_msg:
       return handle_claim(exporter, elem, txinfo, index)

    if "withdraw" in execute_msg:
        return handle_claim(exporter, elem, txinfo, index)

    if "anyone" in execute_msg and "anyone_msg" in execute_msg["anyone"]:
        msg = execute_msg["anyone"]["anyone_msg"]

        if "withdraw_voting_tokens" in msg:
            return handle_governance_unstake(exporter, elem, txinfo, index)

        if "claim_rewards" in msg:
            return handle_claim(exporter, elem, txinfo, index)

        if "cast_vote" in msg:
            return handle_simple(exporter, txinfo, TX_TYPE_VOTE)

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send["msg"]

        if "deposit" in msg:
            return handle_vault_swap(exporter, elem, txinfo, index)

        if "withdraw" in msg:
            return handle_vault_swap(exporter, elem, txinfo, index)

    print("Nexus!")
    return True

def handle_vault_swap(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    assert(len(transfers_out) == 1)
    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    if len(transfers_in) == 0:
        row = make_stake_tx(txinfo, sent_amount, sent_currency, txid)
        exporter.ingest_row(row)
        return

    received_amount, received_currency = util_terra._convert(*transfers_in[0])

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency, txid)
    exporter.ingest_row(row)

def handle_claim(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)
