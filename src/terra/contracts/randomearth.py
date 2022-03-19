# known contracts from protocol
CONTRACTS = [
    # Settlement
    "terra1eek0ymmhyzja60830xhzm7k7jkrk99a60q2z2t",
    # Social - Set like, etc
    "terra1ew29656rv53pg4kpgn44gzy4y0mgzzgqg6k2cx",
]

def handle(exporter, elem, txinfo, contract):
    print(f"Random Earth! {contract}")
    #print(elem)
