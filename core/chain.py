import block
from hashutils import hasProofOfWork, generateHash

from typing import Dict, Tuple, List


class ChainException(Exception):
    """
    Exception class for additions to the chain
    """


class NoParentException(ChainException):
    pass


class DuplicateBlockException(ChainException):
    pass


class Chain:
    def __init__(
            self, persistentFilename=None) -> None:
        self.blocks: Dict[str, block.Block]
        self.blocks = {}
        genesisBlock = block.genesisBlock()
        self.blocks[genesisBlock.hash] = genesisBlock
        
        # The head should always point to the longest and
        # oldest chain.
        self.head = genesisBlock

    def addBlock(self, nextBlock: block.Block) -> None:
        """
        Adds a single block to the chain.
        """
        if nextBlock.hash in self.blocks:
            raise DuplicateBlockException("Duplicate block found when adding to chain.")

        previousBlock = self.getPreviousBlock(nextBlock)
        if previousBlock is None:
            raise NoParentException(
                "New block's previous block is not in the current chain.")

        isVerified, msg = verifyNextBlock(previousBlock, nextBlock)
        if not isVerified:
            raise ChainException(
                "New block could not be verified." +
                "\n" + "Message: " + msg)

        # Creates a new fork in the chain if the next block's previous block
        # does exists in the current chain.
        self.blocks[nextBlock.hash] = nextBlock

        # If the new block increases the length of the current chain, then have
        # head point to this block.
        if nextBlock.index > self.head.index:
            self.head = nextBlock

    def addBlocks(self, newBlocks: List[block.Block]) -> None:
        """
        Adds. a list of blocks to the chain. They will be applied in
        the order of appearance in the list. In the case where the list
        is corrupt, the blocks will be removed from the chain.
        """
        for i in range(len(newBlocks)):
            newBlock = newBlocks[i]
            try:
                self.addBlock(newBlock)
            except ChainException as e:
                for j in range(i):
                    del self.blocks[newBlocks[i].hash]
                raise e
    
    def getChildren(self, parent: block.Block) -> List[block.Block]:
        """
        Returns all the children starting from the parent all the way
        down the chain until the head is reached. If the parent is not
        in the longest chain, then the entire longest chain is returned.

        The order of the returned children is from the oldest to the newest
        block.
        """
        if parent.index > self.head.index:
            return []

        if parent.index < 0:
            raise ChainException("Parent index is negative.")
        
        children: List[block.Block]
        children = []
        child = self.head
        while child.index > 0 and parent.hash != child.hash:
            children.append(child)
            child = self.getPreviousBlock(child)

        children.reverse()
        return children
    

    def getAncestors(self, child: block.Block, n=-1) -> List[block.Block]:
        """
        Returns a n blocks starting from the child and going
        towards the genesis block. If n is negative or unspecified,
        the entire chain will be returned. If the child block is
        None, then the head block is used instead.
        """
        longestChain: List[block.Block]
        longestChain = []
        if n == 0:
            return longestChain

        while n != 0 and child.index > 0:
            longestChain.append(child)

            child = self.getPreviousBlock(child)
            if child is None:
                raise NoParentException(
                    "Ancestors of block do not exist in chain")
            n -= 1
        
        return longestChain

    def getPreviousBlock(self, currentBlock: block.Block) -> block.Block:
        """
        Returns the previous block if it is in the chain
        """
        previousHash = currentBlock.previousHash
        if previousHash in self.blocks:
            return self.blocks[previousHash]

        return None


def verifyNextBlock(
        previousBlock: block.Block,
        nextBlock: block.Block) -> Tuple[bool, str]:
    if nextBlock.index != previousBlock.index + 1:
        return False, "Invalid index. Current: {}, Next {}".format(
            previousBlock.index, nextBlock.index)

    if nextBlock.previousHash != previousBlock.hash:
        return False, "Invalid previous hash. Current {}, Next {}".format(
            previousBlock.hash, nextBlock.previousHash)

    nextHash = generateHash(
        index=previousBlock.index + 1,
        timestamp=nextBlock.timestamp,
        data=nextBlock.data,
        noonce=nextBlock.noonce,
        previousHash=previousBlock.hash)

    if nextHash != nextBlock.hash:
        return False, "Invalid block hash. Current {}, Expected {}".format(
            nextBlock.hash, nextHash)

    if not hasProofOfWork(nextBlock.hash):
        return False, "Block does not have a valid proof of work."

    return True, ""

