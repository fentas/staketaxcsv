from cronos.constants import CUR_CRONOS, EXCHANGE_CRONOS_BLOCKCHAIN
from common.TxInfo import TxInfo as CommonTxInfo


class TxInfo(CommonTxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url):
        super().__init__(txid, timestamp, fee, CUR_CRONOS, wallet_address, EXCHANGE_CRONOS_BLOCKCHAIN, url)
