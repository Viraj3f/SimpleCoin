import json
from typing import List, cast
from core.transaction import Transaction, createTransaction, createFromDictionary

from Crypto.Hash import SHA256


class BlockException(Exception):
    pass


class Block:
    """
    A Block that exists in the blockchain.
    """
    def __init__(
            self,
            index: int,
            timestamp: float,
            transactions: List[Transaction],
            noonce: int,
            previousHash: str) -> None:

        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previousHash = previousHash
        self.noonce = noonce
        self.hash = hashBlock(
            index=index,
            timestamp=timestamp,
            transactions=transactions,
            noonce=noonce,
            previousHash=previousHash)
    
    def asJSON(self) -> str:
        d = {
            "hash": self.hash,
            "index": self.index,
            "timestamp": self.timestamp,
            "noonce": self.noonce,
            "previousHash": self.previousHash,
            "transactions": [],
        }

        for transaction in self.transactions:
            dTransactions = cast(List[Transaction], d["transactions"])
            dTransactions.append(transaction.asDict())

        return json.dumps(d, indent=4)

    def __repr__(self) -> str:
        return self.asJSON()

    def __eq__(self, other: object):
        if isinstance(self, other.__class__):
            lhs = hashBlock(
                self.index,
                self.timestamp,
                self.transactions,
                self.noonce,
                self.previousHash
            )

            other = cast(Block, other)
            rhs = hashBlock(
                other.index,
                other.timestamp,
                other.transactions,
                other.noonce,
                other.previousHash
            )
            return lhs == rhs
        return NotImplemented


def hashBlock(
        index: int,
        timestamp: float,
        transactions: List[Transaction],
        noonce: int,
        previousHash: str) -> str:
    """
    Generates a SHA256 hash for the given data inside a block.
    """
    # Serialize the block's data by encoding it using utf8.
    combinedTransaction = \
        "".join([transaction.hash for transaction in transactions])

    serialized = \
        "{}{}{}{}".format(
            index,
            timestamp,
            combinedTransaction,
            noonce,
            previousHash) \
        .encode('utf-8')
    return SHA256.new(serialized).hexdigest()


def genesisBlock() -> Block:
    """
    Returns the hard-coded genesis block, which is the first Block in
    everybody's chain.
    """
    f = open("./core/genesisKey/publicKey.der")
    genesisAddress = f.read()
    f.close()
    genesisTimestamp = 1514689482.0

    genesisTransaction = createTransaction(
        outputAddresses=[genesisAddress],
        outputAmounts=[1000],
        timestamp=genesisTimestamp
    )

    return Block(
        index=0,
        timestamp=1514689482.0,
        transactions=[genesisTransaction],
        noonce=0,
        previousHash=""
    )


def createFromJSON(jsonBlock: str) -> Block:
    deserialized = json.loads(jsonBlock)

    transactions: List[Transaction] = []
    for transactionDict in deserialized["transactions"]:
        transactions.append(createFromDictionary(transactionDict)) 

    obj = Block(
        index=deserialized["index"],
        transactions=transactions,
        timestamp=deserialized["timestamp"],
        noonce=deserialized["noonce"],
        previousHash=deserialized["previousHash"])

    if deserialized["hash"] != obj.hash:
        raise BlockException("Serialized block hash is invalid.")

    return obj
