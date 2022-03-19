# known contracts from protocol
CONTRACTS = [
    # VKR Token
    "terra1dy9kmlm4anr92e42mrkjwzyvfqwz66un00rwr5",
    # VKR Staking
    "terra1w6xf64nlmy3fevmmypx6w2fa34ue74hlye3chk",
    # VKR Staking (Terra Swap)
    "terra1ude6ggsvwrhefw2dqjh4j6r7fdmu9nk6nf2z32",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Valkyrie {contract}")
    #print(elem)
