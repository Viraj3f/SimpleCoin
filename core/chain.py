from typing import Dict, Tuple, List, cast, Set

from core.settings import MIN_TRANSACTION_AMOUNT, COINBASE_REWARD
from core.settings import MAX_TRANSACTIONS_PER_BLOCK
import core.block as block
from core.mine import hasProofOfWork
import core.transaction as transaction


class ChainException(Exception):
    """
    Exception class for additions to the chain
    """


class NoParentException(ChainException):
    pass


class DuplicateBlockException(ChainException):
    pass


class UTXOException(ChainException):
    pass


class UTXOManager:
    """
    The UTXO manager provides access to get referenced transactions from
    new transactions.

    It is implelmented as a dictionary mapping from transation hash to
    a tuple pair of transaction and a list of unspent indices.

    Note: None of these methods validate that the transaction's hash
    matches the corresponding data.
    """
    def __init__(self):
        self.utxo: Dict[str, Tuple[transaction.Transaction, Set[int]]] = {}

    def spend(self, newTransaction: transaction.Transaction) -> None:
        """
        Spends a transaction and updates the internal cache of utxos.

        A transaction should be verified before it is spent. If this is not
        the case, then it could create an invalid and confusing utxo state.
        Spent transactions are invalid.

        """
        for tInput in newTransaction.inputs:
            self._spendInput(tInput)

        unspentOutputIndices = set(range(len(newTransaction.outputs)))
        self.utxo[newTransaction.hash] = (newTransaction, unspentOutputIndices)

    def canSpend(
            self,
            newTransaction: transaction.Transaction) -> Tuple[bool, str]:
        """
        Verifies if a transaction can be spent based on the current UTXO cache.
        This does not account for duplicate inputs, since that can be
        done elsewhere.
        """
        inputAmounts = 0
        isCoinbase = len(newTransaction.inputs) == 0 \
            and len(newTransaction.outputs) == 1

        for i in range(len(newTransaction.inputs)):
            tInput = newTransaction.inputs[i]
            referenced = self._getReference(tInput)
            if referenced is None:
                return False, "Referenced UTXO does not exist."

            # Verify that the signature is correct
            isValid, msg = transaction.verifyTransactionInput(
                referenced, newTransaction, i)
            if not isValid:
                return False, msg

            inputAmounts += \
                referenced.outputs[tInput.referencedOutputIndex].amount

        outputAmounts = \
            sum([output.amount for output in newTransaction.outputs])

        if not isCoinbase and inputAmounts != outputAmounts:
            return False, "Input amounts to do not match output amounts"

        return True, ""

    def revert(self, tx: transaction.Transaction):
        """
        Reverts the effect of a transaction from a UTXO.
        If the transaction has not been "spent" yet, then using this method
        may cause the internal cache to become invalid.
        """
        for tInput in tx.inputs:
            entry = self.utxo.get(tInput.referencedHash, None)
            if entry is None:
                raise UTXOException(
                    "Reference from reverted transaction does not exist.")

            unspentOutputIndices = cast(Set[int], entry[1])
            if tInput.referencedOutputIndex in unspentOutputIndices:
                raise UTXOException("Transaction index is already inspent.")

            unspentOutputIndices.add(tInput.referencedOutputIndex)

        del self.utxo[tx.hash]

    def _getReference(
            self,
            transactionInput: transaction.TransactionInput) \
            -> transaction.Transaction:
        """
        Gets a referenced transaction from the transaction input.

        When spending a transaction input - do NOT use this method.
        This does not update the internal cache of utxo objects. Instead,
        use the spend() method instead.
        """
        entry = self.utxo.get(transactionInput.referencedHash, None)
        if entry is None:
            return None

        tx = entry[0]
        unspentOutputIndices = cast(Set[int], entry[1])

        if transactionInput.referencedOutputIndex in unspentOutputIndices:
            return tx

        return None

    def _spendInput(self, transactionInput: transaction.TransactionInput):
        """
        Spends a UTXO. Will update the internal cache.
        """
        entry = self.utxo.get(transactionInput.referencedHash, None)
        if entry is None:
            raise UTXOException("Input can not be spent: Invalid hash.")

        tx = entry[0]
        unspentOutputIndices = cast(Set[int], entry[1])
        if transactionInput.referencedOutputIndex in unspentOutputIndices:
            unspentOutputIndices.remove(transactionInput.referencedOutputIndex)
        else:
            raise UTXOException(
                "Input can not be spent: matching " +
                "hash does not have spendable index.")


class Chain:
    def __init__(
            self, persistentFilename=None) -> None:
        # Blocks is a mapping from block hash to block objects
        self.blocks: Dict[str, block.Block] = {}

        # UTXO is a mapping from transaction hash to transaction objects
        self.utxo = UTXOManager()

        # The head should always point to the longest and
        # oldest chain.
        self.head = block.genesisBlock()
        self.blocks[self.head.hash] = self.head

        for tx in self.head.transactions:
            self.utxo.spend(tx)

    def addBlock(self, nextBlock: block.Block) -> None:
        """
        Adds a single block to the chain.
        """
        if nextBlock.hash in self.blocks:
            raise DuplicateBlockException(
                "Duplicate block found when adding to chain.")

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

        if nextBlock.index > self.head.index:
            self._updateUTXOAndHead(nextBlock)


    def _updateUTXOAndHead(self, nextBlock):
        """
        Updated the UTXO for a block being added to the the end of the chain
        of the main chain.

        When a fork becomes the main chain, the UTXO from the current main chain
        are reverted and the new forks outputs are spent.
        """
        if nextBlock.index != self.head.index + 1:
            raise ChainException("Block added to block chain index is invalid")

        # Handle the fork in the rare case where the forked chain becomes
        # the main chain.
        oldChain: List[block.Block] = []
        newChain: List[block.Block] = []
        newChain.append(nextBlock)

        oldParent = self.head
        newParent = self.getPreviousBlock(nextBlock)
        while oldParent.hash != newParent.hash:
            for tx in reversed(oldParent.transactions):
                self.utxo.revert(tx)

            oldChain.append(oldParent)
            newChain.append(newParent)

            oldParent = self.getPreviousBlock(oldParent)
            newParent = self.getPreviousBlock(newParent)

        for i in range(len(newChain) - 1, -1, -1):
            transactions = newChain[i].transactions
            for j in range(len(transactions)):
                tx = transactions[j]
                canSpend, msg = self.utxo.canSpend(tx)
                if canSpend:
                    self.utxo.spend(tx)
                else:
                    # An invalid transaction was found. This means that
                    # all the new transactions need to be reverted,
                    # the old ones respent, and the invalid block deleted.

                    # Revert the transactions just added from the current block.
                    for txIndex in range(j - 1, -1, -1):
                        self.utxo.revert(transactions[txIndex])
                    
                    # Revert the transacation from the blocks added earlier.
                    for blockIndex in range(i + 1, len(newChain)):
                        for tx in reversed(newChain[blockIndex].transactions):
                            self.utxo.revert(tx)
                    
                    # Delete the children blocks from the invalid block
                    # as well as the :nvalid block itself from the chain.
                    for k in range(i, -1, -1):
                        del self.blocks[newChain[k].hash]
                    
                    for oldBlock in reversed(oldChain):
                        for tx in reversed(oldBlock.transactions):
                            self.utxo.spend(tx)
                    
                    raise UTXOException(msg)

        # If the new block increases the length of the current chain, then have
        # head point to this block. The verifyNextBlock method should check 
        # that the new index is not out too large.
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
    """
    Verifies whether a block can syntactically can be added to the chain.
    Once a block is added to the chain with this method called, the only
    remaining check is the "canSpend" method in the UTXO.
    """
    if nextBlock.index != previousBlock.index + 1:
        return False, "Invalid index. Current: {}, Next {}".format(
            previousBlock.index, nextBlock.index)

    if nextBlock.previousHash != previousBlock.hash:
        return False, "Invalid previous hash. Current {}, Next {}".format(
            previousBlock.hash, nextBlock.previousHash)

    nextHash = block.hashBlock(
        index=previousBlock.index + 1,
        timestamp=nextBlock.timestamp,
        transactions=nextBlock.transactions,
        noonce=nextBlock.noonce,
        previousHash=previousBlock.hash)

    if nextHash != nextBlock.hash:
        return False, "Invalid block hash. Current {}, Expected {}".format(
            nextBlock.hash, nextHash)

    if not hasProofOfWork(nextBlock.hash):
        return False, "Block does not have a valid proof of work."

    return verifyTransactionsSyntax(nextBlock.transactions)


def verifyTransactionsSyntax(
    transactions: List[transaction.Transaction]) -> Tuple[bool, str]:
    """
    Verifies if a transaction is syntactically correct and contains
    no duplicates. This operation is pretty expensive, so it only needs
    to be ran once. The list of transactions here are ones that will be
    included in a block.
    """
    if len(transactions) == 0 or len(transactions) > MAX_TRANSACTIONS_PER_BLOCK:
        return False, "Number of transactions is invalid."

    txHashes: Set[str] = set()
    referencedHashes: Set[str] = set()
    hasCoinbase = False

    for tx in transactions:
        expectedHash = transaction.Transaction.createHash(
            inputs=tx.inputs,
            outputs=tx.outputs,
            timestamp=tx.timestamp
        )

        if tx.hash != expectedHash:
            return False, \
                "Transaction hash {} does not match expected {}".format(
                    tx.hash, expectedHash)

        if tx.hash in txHashes:
            return False, "Duplicate transaction objects found. Hash: {}".format(
                tx.hash)
        else:
            txHashes.add(tx.hash)

        # Handle coinbase
        if len(tx.inputs) == 0:
            if len(tx.outputs) == 0:
                return False, "No inputs in outputs found in transaction object."

            # Coinbase transaction found
            if len(tx.outputs) == 1:
                if not hasCoinbase:
                    if tx.outputs[0].amount > COINBASE_REWARD:
                        return False, "Coinbase reward is too large: {}".format(
                            tx.outputs[0].amount
                        )

                    hasCoinbase = True

                    if len(transactions) == 1:
                        return False, "Transactions only have one coinbase."
                else:
                    return False, "Multiple coinbase transactions found."
            else:
                return False, "Coinbase contains too many outputs."

        for tInput in tx.inputs:
            if tInput.referencedHash + str(tInput.referencedOutputIndex) in referencedHashes:
                return False, "Multiple inputs for utxo {} with index {}".format(
                    tInput.referencedHash, tInput.referencedOutputIndex)
            else:
                referencedHashes.add(tInput.referencedHash + str(tInput.referencedOutputIndex))

        for tOutput in tx.outputs:
            if tOutput.amount < MIN_TRANSACTION_AMOUNT:
                return False, \
                    "Output amount '{}' is less than the minimum reward." \
                    .format(tOutput.amount)

    return True, ""