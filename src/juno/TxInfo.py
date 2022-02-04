from juno.constants import CUR_JUNO, EXCHANGE_JUNO_BLOCKCHAIN
from common.TxInfo import TxInfo as CommonTxInfo


class TxInfo(CommonTxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url):
        super().__init__(txid, timestamp, fee, CUR_JUNO, wallet_address, EXCHANGE_JUNO_BLOCKCHAIN, url)
