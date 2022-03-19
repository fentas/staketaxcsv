# known contracts from protocol
CONTRACTS = [
    # Governance
    "terra1xu8utj38xuw6mjwck4n97enmavlv852zkcvhgp",
    # Staking,
    "terra19nek85kaqrvzlxygw20jhy08h3ryjf5kg4ep3l",
    # Pylon $TWD Pre-sale Swap Blunder
    "terra15fgzzle2em5m6w4ps6sm7htvm829pwhwe5t2nl",
    # PSI Swap
    "terra12k0p3qvfhy6j5e3ef8kzusy29lzwykk5d95kk5",
    # Pylon bPsiDP-24m Token / bPsiDP-24m
    "terra1zsaswh926ey8qa5x4vj93kzzlfnef0pstuca0y",
]

def handle(exporter, elem, txinfo, contract):
    print(f"PYLON! {contract}")
    #print(elem)
