# known contracts from protocol
CONTRACTS = [
    # Wormhole webETH Token
    "terra1u5szg038ur9kzuular3cae8hq6q5rk5u27tuvz",
    # Wrapped Registry
    "terra10nmmwe8r3g99a9newtqa7a75xfgs2e8z87r2sf",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Wormhole! {contract}")
    #print(elem)
