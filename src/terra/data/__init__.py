import os
import logging
import requests
import json

NAMED_ACCOUNTS_FILE = "src/terra/data/named_accounts.json"
CONTRACTS_FILE = "src/terra/data/contracts.json"
CONTRACTS_MAINNET_FILE = "src/terra/data/contracts_mainnet.json"
ADDRESSES_FILE = "src/terra/data/addresses.json"

def _query_names(use_cache=True):
    if use_cache:
        if os.path.exists(NAMED_ACCOUNTS_FILE):
            with open(NAMED_ACCOUNTS_FILE, "r") as f:
                data = json.load(f)
            return data

    logging.info("Fetching all named accounts from extraterrestrial")
    response = requests.get("https://extraterra-assets.s3.us-east-2.amazonaws.com/named_accounts.json")
    data = response.json()

    with open(NAMED_ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return data

def _query(use_cache=True):
    if use_cache:
        if os.path.exists(CONTRACTS_FILE):
            with open(CONTRACTS_FILE, "r") as f:
                data = json.load(f)
            with open(CONTRACTS_MAINNET_FILE, "r") as f:
                data["mainnet"] = {**data["mainnet"], **json.load(f)}
            with open(CONTRACTS_MAINNET_FILE, "r") as f:
                data["mainnet"] = {**data["mainnet"], **json.load(f)}
            with open(ADDRESSES_FILE, "r") as f:
                data["mainnet"] = {**data["mainnet"], **json.load(f)}

            return data

    logging.info("Fetching all contracts from extraterrestrial")
    response = requests.get("https://extraterra-assets.s3.us-east-2.amazonaws.com/contracts.json")
    data = response.json()

    with open(CONTRACTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return data

def protocol_contracts(name, chain="mainnet"):
    contracts = _query()[chain]
    return [contract for contract, info in contracts if info["protocol"] == name]

def contract_info(addr, chain="mainnet"):
    contracts = _query()[chain]
    return contracts[addr] if addr in contracts else None

def named_address(addr, chain="mainnet"):
    names = _query_names()[chain]
    return names[addr] if addr in names else ""
