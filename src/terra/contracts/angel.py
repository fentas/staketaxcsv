from terra import util_terra
from terra.col4 import (
    handle_reward_contract,
    handle_governance,
)
from common.make_tx import (
    make_reward_tx,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    if "claim" in execute_msg:
       return handle_reward_contract.handle_airdrop(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        # Governance
        if "stake_voting_tokens" in msg:
            return handle_governance.handle_governance_stake(exporter, elem, txinfo, index)

    print(f"Angel Protocol!")
    return True


def handle_claim(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_in) == 1)

    amount, currency = util_terra._convert(*transfers_in[0])

    row = make_reward_tx(txinfo, amount, currency, txid)
    exporter.ingest_row(row)
