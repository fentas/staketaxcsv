import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)


def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)


    execute_type = _execute_type(elem, txinfo, index)
    logging.info("[terraland] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type