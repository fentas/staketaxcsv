# known contracts from protocol
CONTRACTS = [
    # Pylon MINE Token - MINE
    "terra1kcthelkax4j9x8d3ny6sdag0qmxxynl3qtcrpy",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Mine! {contract}")
    #print(elem)
