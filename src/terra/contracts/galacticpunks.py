import logging
from terra import util_terra
from terra.col4.handle_randomearth import (
    handle_revoke_order,
    handle_mint_nft,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    print(execute_msg)

    if "revoke" in execute_msg:
        return handle_revoke_order(exporter, elem, txinfo, index)

    if "mint_nft" in execute_msg:
        handle_mint_nft(exporter, elem, txinfo)
        return False

    print(f"galacticpunks! {index}")
    return True
