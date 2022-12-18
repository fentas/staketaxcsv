from terra import util_terra
from terra.col4 import (
    handle_governance,
)
from terra.make_tx import (
    make_gov_stake_tx, 
    make_gov_unstake_tx,
)
from common.make_tx import (
    make_just_fee_txinfo,
    make_just_fee_tx,
    make_reward_tx,
)

# known contracts from protocol
CONTRACTS = [
    # Blue Chip
    "terra1r2vv8cyt0scyxymktyfuudqs3lgtypk72w6m3m",
]

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    if "allocate_user_rewards" in execute_msg:
        return False
    
    if "queue_undelegate" in execute_msg:
        return handle_fee(exporter, txinfo, "queue undelegate")

    if "deposit" in execute_msg:
        return handle_stake(exporter, elem, txinfo, index)
        # return handle_governance.handle_governance_stake(exporter, elem, txinfo, index)
    
    if "withdraw_funds_to_wallet" in execute_msg:
        return handle_withdraw_staking(exporter, elem, txinfo, index)

    if "withdraw_airdrops" in execute_msg:
        return handle_withdraw_airdrops(exporter, elem, txinfo, index)

    print(f"Stader!")
    quit()
    return True

def handle_fee(exporter, txinfo, comment):
    row = make_just_fee_txinfo(txinfo)
    row.comment += f" *{comment}"
    exporter.ingest_row(row)

def handle_withdraw_airdrops(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)

    for transfer in transfers_in:
        amount, currency = util_terra._convert(*transfer)
        row = make_reward_tx(txinfo, amount, currency, txid)
        exporter.ingest_row(row)


def handle_withdraw_staking(exporter, elem, txinfo, index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])
    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)

    # fee's
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    if "protocol_fee" in from_contract:
        fee = from_contract["protocol_fee"][0]
        fee_amount = util_terra._float_amount(fee, currency)
        row = make_just_fee_tx(txinfo, fee_amount, currency)
        row.comment = " *withdraw fee"
        exporter.ingest_row(row)

def handle_stake(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)
    amount, currency = util_terra._convert(*transfers_out[0])

    txinfo.comment += " - stader luna stake"
    row = make_gov_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)