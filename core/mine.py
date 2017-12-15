import time

from block import Block
from hashutils import hasProofOfWork, generateHash


def generateNextBlock(previousBlock: Block, nextBlockData: str) -> Block:
    """
    Attempts to generate the next block in given new data
    """
    nextIndex = previousBlock.index + 1
    nextTimestamp = time.time()
    nextBlockData = nextBlockData
    noonce = 0

    while True:
        hash = generateHash(
            nextIndex,
            nextTimestamp,
            nextBlockData,
            noonce,
            previousBlock.hash)
        if hasProofOfWork(hash):
            break
        noonce += 1

    nextBlock = \
        Block(
            index=nextIndex,
            timestamp=nextTimestamp,
            data=nextBlockData,
            noonce=noonce,
            previousHash=previousBlock.hash)

    return nextBlock
