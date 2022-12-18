from terra import util_terra
from terra.col4 import (
    handle_reward_contract,
)
from common.make_tx import (
    make_reward_tx,
    make_transfer_in_tx, 
    make_unknown_tx, 
    make_transfer_out_tx,
)

from terra.col5.actions.complete_transfer_wrapped import handle_action_complete_transfer_wrapped

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "initiate_transfer" in execute_msg:
        return handle_transfer(exporter, elem, txinfo, index)

    print(f"Wormhole!")
    quit()
    return True


def handle_transfer(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    msg = txinfo.msgs[index]

    transfers_in, transfers_out = msg.transfers

    # Check native coins
    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = util_terra._convert(*transfers_in[0])
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        amount, currency = util_terra._convert(*transfers_out[0])
        row = make_transfer_out_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return

    # Check other coins
    for action in msg.actions:
        print(action)
        if action["action"] == "complete_transfer_wrapped":
            [row] = handle_action_complete_transfer_wrapped(txinfo, action, COMMENT)
            exporter.ingest_row(row)
            return
