import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)
from .borrow import (
    handle_deposit_borrow,
    handle_repay_withdraw,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]
        
        # Mirror Borrow Transactions
        if "open_position" in msg:
            return handle_deposit_borrow(exporter, elem, txinfo)
        if "burn" in msg:
            return handle_repay_withdraw(exporter, elem, txinfo)

    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[mirror] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type