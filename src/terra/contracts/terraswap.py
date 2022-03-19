import logging
from terra import util_terra
from terra.execute_type import (
    _execute_type,
    EXECUTE_TYPE_UNKNOWN,
    EXECUTE_TYPE_SWAP,
    EXECUTE_TYPE_ASSERT_LIMIT_ORDER,
    EXECUTE_TYPE_WITHDRAW_LIQUIDITY,
)

# known contracts from protocol
"""
# Terraswap bLUNA-LUNA LP
"terra1nuy34nwnsh53ygpc4xprlj263cztw7vc99leh2",
# Terraswap ANC-UST LP
"terra1gecs98vcuktyfkrve9czrpgtg0m3aq586x6gzm",
# Terraswap ANC-UST Pair
"terra1gm5p3ner9x9xpwugn9sp6gvhd0lwrtkyrecdn3",
# Nexus Psi-UST Terraswap LP
"terra1q6r8hfdl203htfvpsmyh8x689lp2g0m7856fwd",
# terraswap liquidity token (uLP) / VKR-UST Pair
"terra17fysmcl52xjrs8ldswhz7n6mt37r9cmpcguack",
# TerraWorld TWD-UST LP Token
"terra1c9wr85y8p8989tr58flz5gjkqp8q2r6murwpm9",
# Nexus nETH-Psi Terraswap LP
"terra1y8kxhfg22px5er32ctsgjvayaj8q36tr590qtp",
# terraswap liquidity token
"terra1n3gt4k3vth0uppk0urche6m3geu9eqcyujt88q",
"terra14ffp0waxcck733a9jfd58d86h9rac2chf5xhev",
# MINE-UST Pair
"terra178jydtjvj4gw8earkgnqc80c3hrmqj4kw2welz",
# bLUNA-LUNA Pair
"terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p",
# bETH-UST Pair
"terra1c0afrdc5253tkp5wt7rxhuj42xwyf2lcre0s7c",
"""


def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)
    
    if "swap" in execute_msg:
        return EXECUTE_TYPE_SWAP
    
    if "assert_limit_order" in execute_msg:
        return EXECUTE_TYPE_ASSERT_LIMIT_ORDER

    if "send" in execute_msg:
        msg = execute_msg["send"]["msg"]

        if "swap" in msg:
            return EXECUTE_TYPE_SWAP

        if "withdraw_liquidity" in msg:
            return EXECUTE_TYPE_WITHDRAW_LIQUIDITY

    execute_type = _execute_type(elem, txinfo, index)
    logging.debug("[terraswap] General transaction type=%s txid=%s", execute_type, elem["txhash"])
    return execute_type