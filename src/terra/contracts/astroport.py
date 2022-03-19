"""
CONTRACTS = [
    # Lockdrop (LP's)
    "terra1627ldjvxatt54ydd3ns6xaxtd68a2vtyu7kakj",
    # ANC-UUSD-LP
    "terra1wmaty65yt7mjw6fjfymkd9zsm6atsq82d9arcd",
    # LP Staking
    "terra1ukm33qyqx0qcz7rupv085rgpx0tp5wzkhmcj3f",
]
"""
import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
    EXECUTE_TYPE_BOND_IN_MSG,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "bond" in execute_msg:
        return EXECUTE_TYPE_BOND_IN_MSG

    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[astroport] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type