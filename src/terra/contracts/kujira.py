# known contracts from protocol
CONTRACTS = [
    # Governance
    "terra1s6tqnxqk0mqj80uhjq9h8d5qc64lagn3ljlwkh",
    # Kujira UST-KUJI Staking
    "terra1cf9q9lq7tdfju95sdw78y9e34a6qrq3rrc6dre",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Kujira! {contract}")
    #print(elem)
