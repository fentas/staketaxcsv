import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)
from .zap import (
    handle_zap_into_strategy,
    handle_zap_out_of_strategy,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]
        
        # Apollo
        if "zap_into_strategy" in msg:
            return handle_zap_into_strategy(exporter, elem, txinfo)
        if "zap_out_of_strategy" in msg:
            return handle_zap_out_of_strategy(exporter, elem, txinfo)


    execute_type = _execute_type(elem, txinfo, index)
    logging.info("[apollo] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type