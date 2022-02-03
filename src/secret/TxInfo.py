from secret.constants import CUR_SECRET, EXCHANGE_SECRET_BLOCKCHAIN
from common.TxInfo import TxInfo as CommonTxInfo


class TxInfo(CommonTxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url):
        super().__init__(txid, timestamp, fee, CUR_SECRET, wallet_address, EXCHANGE_SECRET_BLOCKCHAIN, url)
