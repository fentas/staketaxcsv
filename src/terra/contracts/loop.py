# known contracts from protocol
CONTRACTS = [
    # LOOP Token - LOOP
    "terra1nef5jf6c7js9x6gkntlehgywvjlpytm7pcgkn4",
    # Loop Staking
    "terra1cr7ytvgcrrkymkshl25klgeqxfs48dq4rv8j26",
    # Loop IDO (Via StarTerra)
    "terra1wcmquav80s07phd3wc4zkshuv40wmcpurqw5t2",
    # loopswap liquidity token - uLP / loop-loopr
    "terra1p266mp7ahnrnuxnxqxfhf4rejcqe2lmjsy6tuq",
    "terra1eas9qze4j0lhasc6g0hjykvcyksakvsun4ndyv",
    "terra1j6l2m2e2q92zkd9v48cs2l4n74rxn2plphul96",
    "terra1nuuq9qmyqv5td9297fktnf864pvlw9q79f65m8",
    "terra1yy46j5xy7fykt6q58aa4u4y39h4fxc7jke2spd",
    # ... / loop-ust
    "terra1f0nj4lnggvc7r8l3ay5jx7q2dya4gzllez0jw2",
    # LoopFarm - uLP
    "terra1hd7n4mvg7pkgk7y8fzry3uh5m9l3az45dlnps2",
    "terra10s8g4nph6xy77wj26yxdudtxqzec4dk2mhlmua",
    "terra1r6feguefa559986p6pv63du088st83vevvsxff",
    "terra1l9722elh7wucvexw7nclawlnr04t8ktz0muv5e",
    "terra1kvhaxxn6dl82kqppvfug4ggmxyqvcpk6vjz762",
    "terra1nkqjwr3lsya7vhamq53g5hmxnfkdz3ayzqp8y9",
    "terra1a8l9532278f0dn9lg343tqcvumkec26d5ss6mj",
    # LP
    "terra1nx03wv4mqglwkfual4wcyq0lrwa425gr4gz0rj",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Loop! {contract}")
    #print(elem)
