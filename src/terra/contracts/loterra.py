# known contracts from protocol
# https://docs.loterra.io/resources/contract-addresses
CONTRACTS = [
    # LOTA-UST LP (uLP Token)
    "terra1t4xype7nzjxrzttuwuyh9sglwaaeszr8l78u6e",
    # v1: Staking contract LP token address LOTA - UST LP
    "terra1pdslh858spzqrtx2gwr69pzm9m2wrv55aeh742",
    # LOTA v2.1.0
    "terra1q2k29wwcz055q4ftx4eucsq6tg9wtulprjg75w",
    # v1 - get tickets
    "terra1z2vgthmdy5qlz4cnj9d9d3ajtqeq7uzc0acxrp",
]

def handle(exporter, elem, txinfo, contract):
    print('LOTA!')
    #print(elem)
