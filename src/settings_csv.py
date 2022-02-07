import os

# Environment variables (required for each respective report)

SOL_NODE = os.environ.get("SOL_NODE", "https://api.mainnet-beta.solana.com")
ATOM_NODE = os.environ.get("ATOM_NODE", "https://api.cosmos.network")
TERRA_LCD_NODE = os.environ.get("TERRA_LCD_NODE", "https://lcd.terra.dev")
ALGO_INDEXER_NODE = os.environ.get("ALGO_INDEXER_NODE", "https://algoindexer.algoexplorerapi.io")
CRONOS_NODE = os.environ.get("CRONOS_NODE", "https://crypto.org/explorer/api")
SECRET_NODE = os.environ.get("SECRET_NODE", "https://api-secret.cosmostation.io")
BITSONG_NODE = os.environ.get("BITSONG_NODE", "https://api-bitsong.cosmostation.io")

# Optional environment variables
TERRA_FIGMENT_KEY = os.environ.get("TERRA_FIGMENT_KEY", "")

# #############################################################################

TICKER_ATOM = "ATOM"
TICKER_LUNA = "LUNA"
TICKER_SOL = "SOL"
TICKER_OSMO = "OSMO"
TICKER_ALGO = "ALGO"
TICKER_CRONOS = "CRO"
TICKER_SECRET = "SCRT"
TICKER_JUNO = "JUNO"
TICKER_BITSONG = "BTSG"
TICKER_IOTEX = "IOTX"

DONATION_WALLETS = set([
    os.environ.get("DONATION_WALLET_ATOM", ""),
    os.environ.get("DONATION_WALLET_LUNA", ""),
    os.environ.get("DONATION_WALLET_SOL", ""),
    os.environ.get("DONATION_WALLET_OSMO", ""),
    os.environ.get("DONATION_WALLET_ALGO", ""),
])

MESSAGE_ADDRESS_NOT_FOUND = "Wallet address not found"
MESSAGE_STAKING_ADDRESS_FOUND = "Staking address found.  Please input the main wallet address instead."

REPORTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/_reports"
