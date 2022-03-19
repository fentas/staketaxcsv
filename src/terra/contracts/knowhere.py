# known contracts from protocol
CONTRACTS = [
    # Auctions
    "terra1en087uygr8f57vdczvkhy9465t9y6su4ztq4u3",
    # Marketplace
    "terra12v8vrgntasf37xpj282szqpdyad7dgmkgnq60j",
]

def handle(exporter, elem, txinfo, contract):
    print(f"knowhere! {contract}")
    #print(elem)
