from terra import util_terra
from terra.make_tx import (
    make_nft_buy_tx,
)

"""
{
  "minter": "terra1g3r6kk4u7rv3hjfs8nxptskxw5jk3qyvfv0yjx",
  "name": "Galactic Gridz",
  "symbol": "GG"
}
"""
NAME = "Galactic Gridz"
CONTRACT_ADDR = "terra1ygy58urzh826al6ktlskh4z6hnd2aunhcn0cvm"

def handle(exporter, elem, txinfo, index):
    execute_msg = util_terra._execute_msg(elem, index)

    # Nothing to do here - internal
    if "modify_address_whitelist" in execute_msg:
        return False

    if "mint_nft" in execute_msg:
        return handle_mint(exporter, elem, txinfo, index)

    print(f"Galactic Gridz!")
    return True

def handle_mint(exporter, elem, txinfo, index):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid, index=index)
    assert(len(transfers_out) == 1)
    sent_amount, sent_currency = util_terra._convert(*transfers_out[0])

    events = elem["logs"][index]["events_by_type"]["from_contract"]

    token_id = events["token_id"][0]
    nft_currency = "{}_{}".format(CONTRACT_ADDR, token_id)
    row = make_nft_buy_tx(txinfo, sent_amount, sent_currency, nft_currency, NAME)
    exporter.ingest_row(row)