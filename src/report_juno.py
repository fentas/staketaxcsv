"""
usage: python3 report_juno.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/juno*.csv

"""

import json
import logging
import math
import os
import pprint

import juno.api_lcd
import juno.processor
from juno.config import localconfig
from juno.progress import Progress
from common import report_util
from common.Exporter import Exporter
from common.CacheChain import CacheChain
from settings_csv import TICKER_JUNO

LIMIT = 50
MAX_TRANSACTIONS = 1000


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_JUNO)
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_JUNO, wallet_address, exporter, export_format)


def _read_options(options):
    if not options:
        return
    report_util.read_common_options(localconfig, options)

    localconfig.legacy = options.get("legacy", False)
    logging.info("localconfig: %s", localconfig.__dict__)


def txone(wallet_address, txid):
    if localconfig.legacy:
        elem = juno.api_cosmostation.get_tx(txid)
    else:
        elem = juno.api_lcd.get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address)
    juno.processor.process_tx(wallet_address, elem, exporter)
    return exporter


def txhistory(wallet_address, job=None, options=None):
    progress = Progress()
    exporter = Exporter(wallet_address)

    if options:
        _read_options(options)
    if job:
        localconfig.job = job
    if localconfig.cache:
        if CacheChain("juno", wallet_address) is None:
            logging.info("Could not initialize mongodb cache ...")
        else:
            logging.info("Chache txs and contracts to mongodb ...")

    # Fetch transactions
    elems = []
    elems.extend(_fetch_txs(wallet_address, progress))
    elems = _remove_duplicates(elems)

    progress.report_message(f"Processing {len(elems)} juno transactions... ")
    juno.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def _fetch_txs(wallet_address, progress):
    if localconfig.debug:
        debug_file = f"_reports/testjuno.{wallet_address}.json"
        if os.path.exists(debug_file):
            with open(debug_file, "r") as f:
                return json.load(f)

    cache = CacheChain()
    out = []
    offset = 0
    progress.set_estimate(1)

    while offset is not None:
        # todo: how to get total for progress
        message = f"Fetching with offset {offset}"
        progress.report(offset if offset is not None else 1, message)

        elems, offset, _ = juno.api_lcd.get_txs(wallet_address, offset)

        # cache if enabled
        if cache is not None:
            all_unique = cache.insert_txs(elems)
            if all_unique == False:
                break
        else:
            out.extend(elems)

    # fetch txs from cache
    if cache is not None:
        out = list(cache.get_account_txs())

    # Debugging only
    if localconfig.debug:
        with open(debug_file, "w") as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", debug_file)
    return out


def _remove_duplicates(elems):
    out = []
    txids = set()

    for elem in elems:
        if elem["txhash"] in txids:
            continue

        out.append(elem)
        txids.add(elem["txhash"])

    out.sort(key=lambda elem: elem["timestamp"], reverse=True)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
