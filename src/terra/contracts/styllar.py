# known contracts from protocol
CONTRACTS = [
    # Whitelist contract
    "terra1xe5n8aa8xvtqtwtaj6k9fu0kd209thyff3gfuk",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Styllar! {contract}")
    #print(elem)
