from terra import util_terra
from terra.make_tx import make_swap_tx_terra
from common.make_tx import make_just_fee_tx
from terra.util_terra import _asset_to_currency, _float_amount

from common.ExporterTypes import (
    TX_TYPE_FEE_SETTLEMENT,
)

def handle_swap_msgswap(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)

    for i in range(len(transfers_in)):
        received_amount, received_currency = transfers_in[i]
        sent_amount, sent_currency = transfers_out[i]

        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                                 txid=txid, empty_fee=(i > 0))
        exporter.ingest_row(row)


def handle_swap(exporter, elem, txinfo):
    logs = elem["logs"]

    if "coin_received" in logs[0]["events_by_type"]:
        for log in logs:
            _parse_log(exporter, txinfo, log)
    else:
        # older version of data
        from_contract = util_terra._event_with_action(elem, "from_contract", "swap")
        _parse_from_contract(exporter, txinfo, from_contract)


def handle_execute_swap_operations(exporter, elem, txinfo):
    logs = elem["logs"]

    if "coin_received" in logs[0]["events_by_type"]:
        for log in logs:
            _parse_log(exporter, txinfo, log)
    else:
        # older version of data
        _parse_swap_operations(exporter, elem, txinfo)


def _parse_log(exporter, txinfo, log):
    # Parse using from_contract field if exists
    result = _parse_from_contract_if_exists(exporter, txinfo, log)
    if result:
        return

    # Parse using coin_received, coin_spent fields if right info available
    result = _parse_coins(exporter, txinfo, log)
    if result:
        return

    print(txinfo)
    print(log)
    raise Exception("Bad condition in _parse_log()")

#'events_by_type': {'coin_received': {'receiver': ['terra1yqg0wzvkjn7c83ra83ksthwu6vd927kssrhwhn'], 'amount': ['100000uusd']}, 'coin_spent': {'spender': ['terra1fjquyucxhek7ut7h596mwcrhfllyr8mvurfpmx'], 'amount': ['100000uusd']}, 'message': {'action': ['/cosmos.bank.v1beta1.MsgSend'], 'sender': ['terra1fjquyucxhek7ut7h596mwcrhfllyr8mvurfpmx'], 'module': ['bank']}, 'transfer': {'recipient': ['terra1yqg0wzvkjn7c83ra83ksthwu6vd927kssrhwhn'], 'sender': ['terra1fjquyucxhek7ut7h596mwcrhfllyr8mvurfpmx'], 'amount': ['100000uusd']}}
def _parse_coins(exporter, txinfo, log):
    wallet_address = txinfo.wallet_address

    coin_received = log["events_by_type"]["coin_received"]
    coin_spent = log["events_by_type"]["coin_spent"]

    amounts = coin_received["amount"]
    receivers = coin_received["receiver"]
    received = [amounts[i] for i in range(len(amounts)) if receivers[i] == wallet_address]

    amounts = coin_spent["amount"]
    spenders = coin_spent["spender"]
    sent = [amounts[i] for i in range(len(amounts)) if spenders[i] == wallet_address]

    if len(received) == 1 and len(sent) == 1:
        amount_string_received = received[0]
        amount_string_sent = sent[0]

        received_amount, received_currency = util_terra._amount(amount_string_received)
        sent_amount, sent_currency = util_terra._amount(amount_string_sent)

        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return True
    # 99% sure this are fee's in a swap scenario (like coinhall or stt)
    elif len(sent) == 1 and len(receivers) == 1 and len(spenders) == 1:
        amount_string_sent = sent[0]
        sent_amount, sent_currency = util_terra._amount(amount_string_sent)

        row = make_just_fee_tx(txinfo, sent_amount, sent_currency, TX_TYPE_FEE_SETTLEMENT)
        exporter.ingest_row(row)
        return True
    
    return False


def _parse_swap_operations(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    # Determine send amount, currency
    if transfers_out:
        sent_amount, sent_currency = transfers_out[0]
    else:
        sent_amount, sent_currency = _sent(from_contract, txid)

    # Determine receive amount, currency
    if transfers_in:
        receive_amount, receive_currency = transfers_in[0]
    else:
        receive_amount, receive_currency = _received(from_contract, txid)

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    exporter.ingest_row(row)


def _parse_from_contract_if_exists(exporter, txinfo, log):
    from_contract = log["events_by_type"].get("from_contract", None)
    if from_contract:
        _parse_from_contract(exporter, txinfo, from_contract)
        return True
    else:
        return False


def _parse_from_contract(exporter, txinfo, from_contract):
    txid = txinfo.txid

    sent_amount, sent_currency = _sent(from_contract, txid)
    receive_amount, receive_currency = _received(from_contract, txid)

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    exporter.ingest_row(row)


def _sent(from_contract, txid):
    offer_amount = from_contract["offer_amount"][0]
    offer_asset = from_contract["offer_asset"][0]

    # Determine currency
    send_currency = _asset_to_currency(offer_asset, txid)

    # Determine amount
    send_amount = _float_amount(offer_amount, send_currency)

    return send_amount, send_currency


def _received(from_contract, txid):
    last_return_amount = from_contract["return_amount"][-1]
    last_asset = from_contract["ask_asset"][-1]
    last_tax_amount = from_contract["tax_amount"][-1] if "tax_amount" in from_contract else 0

    # Determine currency
    receive_currency = _asset_to_currency(last_asset, txid)

    # Determine amount
    receive_amount = (_float_amount(last_return_amount, receive_currency)
                      - _float_amount(last_tax_amount, receive_currency))

    return receive_amount, receive_currency
