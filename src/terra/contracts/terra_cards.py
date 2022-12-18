import logging
from terra import util_terra
from terra.col4.handle_randomearth import (
    handle_transfer_nft,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    print(execute_msg)

    if "transfer_nft" in execute_msg:
        return handle_transfer_nft(exporter, elem, txinfo, index)

    print(f"Terra Cards! {index}")
    return True
