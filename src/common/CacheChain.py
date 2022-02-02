
import os
import logging
from pymongo import MongoClient, errors, ASCENDING, DESCENDING

MONGODB_URL = os.environ.get("MONGODB_URL")
CHAIN_CONFIG = {
    "terra": {
        "keys": {
            "txhash": "txhash",
            "timestamp": "timestamp"
        },
        "sort": ASCENDING,
        "ignore": ["raw_log"]
    },
    "osmo": {
        "keys": {
            "txhash": "txhash",
            "timestamp": "timestamp"
        },
        "sort": DESCENDING,
        "ignore": ["raw_log"]
    },
}

class CacheChain:
    # keep CacheCain as singleton
    # https://www.python.org/download/releases/2.2/descrintro/#__new__
    def __new__(cls, *args, **kwargs):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        
        # precheck conditions
        if MONGODB_URL is None:
            return None
        
        # precheck arguments if not given return None
        if 'chain' in kwargs:
            args[0] = kwargs['chain']
        if 'account' in kwargs:
            args[1] = kwargs['account']
        if len(args) != 2:
            return None

        cls.__it__ = it = object.__new__(cls)
        it._init(*args, **kwargs)
        return it

    def _init(self, chain, account):
        self.account = account
        self._chain = CHAIN_CONFIG[chain]

        self.mongo = MongoClient(MONGODB_URL)
        self.db = self.mongo[chain]

        self.db.txs.create_index(
            self._chain['keys']['txhash'], 
            name="unique", 
            unique=True
        )
        self.db.account.create_index(
            [('txhash', ASCENDING), ('account', ASCENDING)], 
            name="unique", 
            unique=True
        )
        self.db.contract.create_index(
            "contract", 
            name="unique", 
            unique=True
        )


    def get_tx(self, tx):
        find = {}
        find[self._tx_key] = tx
        return self.db.txs.find_one(find)

    def get_account_txs(self):
        return self.db.account.aggregate([
            {
                "$match": {
                    "account": self.account,
                    "timestamp": { "$gte" : "2021-06-01T2:00:00Z" },
                }
            },
            { "$sort": { "timestamp": self._chain['sort'] } },
            {
                "$lookup": {
                    "from": "txs",
                    "localField": "txhash",
                    "foreignField": self._chain['keys']['txhash'],
                    "as": "tx"
                }
            },
            { "$unwind": "$tx" },
            { "$replaceRoot": { "newRoot": "$tx" } },
        ])

    def tx_exists(self, txhash):
        return True if self._get_tx(txhash) is not None else False

    def insert_txs(self, txs):
        for tx in txs:
            # general cleanup
            for field in self._chain['ignore']:
                del tx[field]

            try:
                result = self.db.txs.insert_one(tx)
            except errors.DuplicateKeyError:
                pass

            try:
                self.db.account.insert_one({
                    "account": self.account,
                    "txhash": tx[self._chain['keys']['txhash']],
                    "timestamp": tx[self._chain['keys']['timestamp']]
                })
            except errors.DuplicateKeyError:
                logging.info("duplicate account tx: %s", tx[self._chain['keys']['txhash']])
                return False

        return True

    def set_contract(self, contract, data):
        self.db.contract.insert_one({
            "contract": contract,
            "data": data
        })
    
    def get_contract(self, contract):
        result = self.db.contract.find_one({
            "contract": contract
        })
        return result['data'] if result is not None else None


