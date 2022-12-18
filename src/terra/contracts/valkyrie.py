from terra import util_terra
from terra.col4 import (
    handle_reward_contract,
)
from terra.col4.handle_governance import (
    handle_governance_unstake, 
    handle_governance_stake,
)
from terra.col4.handle_lp import handle_lp_deposit, handle_lp_withdraw, handle_lp_stake, handle_lp_unstake

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    print(execute_msg)
    if "withdraw" in execute_msg:
        return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo, index)

    if "claim" in execute_msg:
       return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo, index)

    if "unstake_governance_token" in execute_msg:
        return handle_governance_unstake(exporter, elem, txinfo, index)

    if "auto_stake" in execute_msg:
        return handle_lp_deposit(exporter, elem, txinfo, index)

    if "unbond" in execute_msg:
        return handle_lp_unstake(exporter, elem, txinfo, index)

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]
        
        if "stake_governance_token" in msg:
            return handle_governance_stake(exporter, elem, txinfo, index)

        if "unbond" in execute_msg:
            return handle_lp_withdraw(exporter, elem, txinfo, index)

    quit()
    print(f"Valkyrie!")
    return True