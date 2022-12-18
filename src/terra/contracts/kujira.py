import logging
from terra import util_terra
from terra.make_tx import (
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_stake_tx,
    make_gov_stake_tx
)
from common.make_tx import (
    make_reward_tx,
    make_just_fee_txinfo,
)
from terra.col4 import (
    handle_simple,
)
from common.ExporterTypes import (
    TX_TYPE_VOTE,
)
from common.make_tx import make_just_fee_tx

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "register" in execute_msg:
        return handle_fee(exporter, txinfo, "enter campaign")

    if "migrate" in execute_msg:
        return handle_fee(exporter, txinfo, "migrate to sKujira")

    if "vote" in execute_msg:
        handle_simple.handle_simple(exporter, txinfo, TX_TYPE_VOTE)
        return False

    if "withdraw" in execute_msg:
        return handle_withdraw(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        # Governance
        if "bond" in msg:
            return handle_bond(exporter, elem, txinfo, index)

    print("Kujira!")
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_bond(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        # todo: not exactly sure what happend here
        # 0057A477246242A30B2141F124B73A827C9B644578DE33F67C4FD0BF21DECEDE
        for log in elem["logs"]:
            for event in log.get("events", []):
                if event["type"] != "from_contract":
                    continue

                attributes = event["attributes"]
                for i in range(0, len(attributes), 1):
                    attribute = attributes[i]

                    if attribute["key"] == "action" and attribute["value"] == "bond":
                        currency = attributes[0]["value"]
                        amount = attributes[i+1]["value"]
                        sender = attributes[i+2]["value"]

                        if sender == wallet_address:
                            amount, currency = util_terra._convert(amount, currency)
                            row = make_reward_tx(txinfo, amount, currency, txid, empty_fee=True)
                            row.comment += " *airdop(?)"
                            exporter.ingest_row(row)
                            row = make_gov_stake_tx(txinfo, amount, currency, empty_fee=True)
                            exporter.ingest_row(row)
                            return False

def handle_withdraw(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)