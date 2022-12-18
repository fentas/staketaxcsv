import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
)
from .zap import (
    handle_zap_into_strategy,
    handle_zap_out_of_strategy,
)
from terra.col4 import (
    handle_reward_contract,
    handle_governance,
)
from terra.col4.handle_lp import handle_lp_stake, handle_lp_unstake

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    if "claim_phase1" in execute_msg:
       return handle_reward_contract.handle_airdrop(exporter, elem, txinfo, index)
    if "claim" in execute_msg:
       return handle_reward_contract.handle_airdrop(exporter, elem, txinfo, index)

    if "zap_out_of_strategy" in execute_msg:
        handle_zap_out_of_strategy(exporter, elem, txinfo)
        return False
    if "zap_into_strategy" in execute_msg:
        handle_zap_into_strategy(exporter, elem, txinfo)
        return False

    if "withdraw_from_strategy" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]
        
        # Apollo
        if "zap_into_strategy" in msg:
            handle_zap_into_strategy(exporter, elem, txinfo)
            return False
        if "zap_out_of_strategy" in msg:
            handle_zap_out_of_strategy(exporter, elem, txinfo)
            return False

        if "deposit" in msg:
            return handle_lp_stake(exporter, elem, txinfo, index)


    quit()
    print("Apollo!")
    return True