from common.make_tx import make_reward_tx, make_unknown_tx
from terra import util_terra
from terra.make_tx import make_gov_stake_tx, make_gov_unstake_tx


def handle_governance_stake(exporter, elem, txinfo, index=0):
    txid = txinfo.txid

    amount, currency = _extract_amount(elem, txid, "send", index)
    if amount and currency:
        row = make_gov_stake_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)


def handle_governance_unstake(exporter, elem, txinfo, index=0):
    txid = txinfo.txid

    amount, currency = _extract_amount(elem, txid, "transfer", index)
    if amount and currency:
        row = make_gov_unstake_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)


def handle_governance_reward(exporter, elem, txinfo):
    txid = txinfo.txid

    amount, currency = _extract_amount(elem, txid, "transfer")
    if amount and currency:
        row = make_reward_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)


def _extract_amount(elem, txid, target_action, index=0):
    from_contract = elem["logs"][index]["events_by_type"]["from_contract"]

    try:
        actions = from_contract["action"]
        amounts = from_contract["amount"]
        contract_addresses = from_contract["contract_address"]

        for i in range(len(actions)):
            action = actions[i]
            amount_string = amounts[i]
            contract_address = contract_addresses[i]

            if action == target_action:
                currency = util_terra._lookup_address(contract_address, txid)
                amount = util_terra._float_amount(amount_string, currency)

                return amount, currency
    except Exception:
        pass

    try:
        amounts = from_contract["unstake_amount"]
        actions = from_contract["action"]
        for i in range(len(actions)):
            action = actions[i]
            contract_address = contract_addresses[i]

            if action == "transfer":
                currency = util_terra._lookup_address(contract_address, txid)

        amount = util_terra._float_amount(amounts[0], currency)
        return amount, currency
    except Exception:
        pass

    return None, None
