import time
from typing import List

from core.block import Block, hashBlock
from core.transaction import Transaction


def hasProofOfWork(hash: str) -> bool:
    """
    Checks if the first n half-bytes in the hash are zero, where n
    is the difficulty.
    """
    difficulty = 1  # Number of most significant bytes that are zero.
    return int(hash[:difficulty], 16) == 0


def generateNextBlock(
        previousBlock: Block,
        transactions: List[Transaction]) -> Block:
    """
    Attempts to generate the next block in given new data
    """
    nextIndex = previousBlock.index + 1
    nextTimestamp = time.time()
    noonce = 0

    while True:
        hash = hashBlock(
            nextIndex,
            nextTimestamp,
            transactions,
            noonce,
            previousBlock.hash)
        if hasProofOfWork(hash):
            return Block(
                index=nextIndex,
                timestamp=nextTimestamp,
                transactions=transactions,
                noonce=noonce,
                previousHash=previousBlock.hash)
        noonce += 1

    return None
