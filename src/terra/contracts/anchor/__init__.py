import logging
from terra import util_terra
from terra.execute_type import _execute_type

from .bond import (
    handle_bond, 
    handle_unbond, 
    handle_unbond_withdraw,
)
from .borrow import (
    handle_borrow,
    handle_deposit_collateral,
    handle_repay,
    handle_withdraw_collateral,
)
from .earn import (
    handle_anchor_earn_deposit, 
    handle_anchor_earn_withdraw,
)
from terra.handle_lp import (
    handle_lp_stake,
    handle_lp_unstake,
)

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)


    # Borrow Transactions
    if "borrow_stable" in execute_msg:
        return handle_borrow(exporter, elem, txinfo)
    if "repay_stable" in execute_msg:
        return handle_repay(exporter, elem, txinfo)
    
    #if "unlock_collateral" in execute_msg:
    #    return handle_withdraw_collateral(exporter, elem, txinfo)

    # Anchor Earn transactions
    if "deposit_stable" in execute_msg:
        return handle_anchor_earn_deposit(exporter, elem, txinfo)

    # Bond transactions
    if "bond" in execute_msg:
        return handle_bond(exporter, elem, txinfo)
    if "withdraw_unbonded" in execute_msg:
        return handle_unbond_withdraw(exporter, elem, txinfo)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        # Borrow Transactions
        if "deposit_collateral" in msg:
            return handle_deposit_collateral(exporter, elem, txinfo)

        # Bond transactions
        if "unbond" in msg:
            return handle_unbond(exporter, elem, txinfo)

        # Earn transactions
        #if "deposit_stable" in msg:
        #    return handle_anchor_earn_deposit(exporter, elem, txinfo)
        if "redeem_stable" in msg:
            return handle_anchor_earn_withdraw(exporter, elem, txinfo)

    # Nothing to do here - internal
    if "lock_collateral" in execute_msg:
        return
    if "unlock_collateral" in execute_msg:
        return
    
    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[anchor] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type