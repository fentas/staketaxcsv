# known contracts from protocol
CONTRACTS = [
    # NFT - Meteor Dust
    "terra1p70x7jkqhf37qa7qm4v23g4u4g8ka4ktxudxa7",
    # NFT - Eggs
    "terra1k0y373yxqne22pc9g7jvnr4qclpsxtafevtrpg",
    # NFT - Dragons
    "terra1vhuyuwwr4rkdpez5f5lmuqavut28h5dt29rpn6",
    # NFT - Loot
    "terra14gfnxnwl0yz6njzet4n33erq5n70wt79nm24el",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Levana! {contract}")
    #print(elem)
    return True
