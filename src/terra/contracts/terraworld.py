# known contracts from protocol
CONTRACTS = [
    # Staking
    "terra10eyxljyqkcvhs4dgr534hk0wehc28tz6gwnh8a",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Terra World! {contract}")
    #print(elem)
