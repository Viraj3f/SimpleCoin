import json

from hashutils import generateHash


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
            data: str,
            noonce: int,
            previousHash: str) -> None:

        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previousHash = previousHash
        self.noonce = noonce
        self.hash = generateHash(
            index=index,
            timestamp=timestamp,
            data=data,
            noonce=noonce,
            previousHash=previousHash)

    def json(self) -> str:
        return json.dumps({
            "hash": self.hash,
            "index": self.index,
            "timestamp": self.timestamp,
            "noonce": self.noonce,
            "data": self.data,
            "previousHash": self.previousHash,
        }, indent=1)

    def __repr__(self) -> str:
        return self.json()

    def __eq__(self, other: object):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented


def genesisBlock() -> Block:
    """
    Returns the hard-coded genesis block, which is the first Block in
    everybody's chain.
    """
    return Block(index=0, timestamp=0, data="", noonce=0, previousHash="")


def createFromJSON(jsonBlock: str) -> Block:
    deserialized = json.loads(jsonBlock)
    obj = Block(
        index=deserialized["index"],
        data=deserialized["data"],
        timestamp=deserialized["timestamp"],
        noonce=deserialized["noonce"],
        previousHash=deserialized["previousHash"])

    if deserialized["hash"] != obj.hash:
        raise BlockException("Serialized block hash is invalid.")

    return obj
