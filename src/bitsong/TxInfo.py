from bitsong.constants import CUR_BITSONG, EXCHANGE_BITSONG_BLOCKCHAIN
from common.TxInfo import TxInfo as CommonTxInfo


class TxInfo(CommonTxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url):
        super().__init__(txid, timestamp, fee, CUR_BITSONG, wallet_address, EXCHANGE_BITSONG_BLOCKCHAIN, url)
