import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
    EXECUTE_TYPE_SWAP,
)
from .borrow import (
    handle_deposit_borrow,
    handle_repay_withdraw,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "execute_order" in execute_msg:
        return EXECUTE_TYPE_SWAP

    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[miaw] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type