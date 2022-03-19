# known contracts from protocol
CONTRACTS = [
    # Nexus Governance
    "terra1xrk6v2tfjrhjz2dsfecj40ps7ayanjx970gy0j",
    # Nexus Psi-UST Terraswap Staking
    "terra12kzewegufqprmzl20nhsuwjjq6xu8t8ppzt30a",
    # Nexus bLuna Vault
    "terra1cda4adzngjzcn8quvfu2229s8tedl5t306352x",
    # Nexus nLuna rewards
    "terra1hjv3quqsrw3jy7pulgutj0tgxrcrnw2zs2j0k7",
    # Nexus nLuna
    "terra10f2mt82kjnkxqj2gepgwl637u2w4ue2z5nhz5j",
    # Nexus nETH
    "terra178v546c407pdnx5rer3hu8s2c0fc924k74ymnn",
    # Nexus nLuna-Psi Terraswap Staking
    "terra1hs4ev0ghwn4wr888jwm56eztfpau6rjcd8mczc",
    # Nexus nETH-Psi Terraswap Staking
    "terra1lws09x0slx892ux526d6atwwgdxnjg58uan8ph",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Nexus! {contract}")
    #print(elem)
