import unittest
import time
from core import block, chain, transaction, mine
from test import private1, private2, private3, public1, public2, public3


class TestUTXOManager(unittest.TestCase):
    def test_validSyntax(self):
        timestamp = time.time()
        tx1 = transaction.createTransaction([public1], [1000], timestamp)
        tx2 = transaction.createTransaction(
            [public2, public3],
            [500, 500],
            timestamp,
            [tx1.hash],
            [0],
            [private1])
        txList = [tx1, tx2]
        self.assertTrue(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test valid transactions")

        # Test duplicate transactions
        txList = [tx1, tx1]
        self.assertFalse(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test duplicate transactions")

        # Test invalid hash
        temp = tx1.hash
        txList = [tx1, tx2]
        tx1.hash = tx2.hash
        self.assertFalse(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test invalid hash")
        tx1.hash = temp

        # Test duplicate references
        tx3 = transaction.createTransaction(
            [public2],
            [1000],
            timestamp,
            [tx1.hash],
            [0],
            [private1])
        txList = [tx1, tx2, tx3]
        self.assertFalse(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test duplicate references")

        tx4 = transaction.createTransaction(
            [public2],
            [1000],
            timestamp)
        txList = [tx1, tx2, tx4]

        self.assertFalse(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test multiple coinbase transaction list")

        tx4 = transaction.createTransaction(
            [public2, public3],
            [1000, 1000],
            timestamp)
        txList = [tx2, tx4]
        self.assertFalse(
            chain.verifyTransactionsSyntax(txList)[0],
            "Test multi-output coinbase")

    def test_validUTXO(self):
        manager = chain.UTXOManager()
        # 1 2 and 3 should all start with 1000 SPC
        timestamp = time.time()
        tx1 = transaction.createTransaction([public1], [1000], timestamp)
        tx2 = transaction.createTransaction([public2], [1000], timestamp)
        tx3 = transaction.createTransaction([public3], [1000], timestamp)

        self.assertTrue(manager.canSpend(tx1))
        self.assertTrue(manager.canSpend(tx2))
        self.assertTrue(manager.canSpend(tx3))

        manager.spend(tx1)
        manager.spend(tx2)
        manager.spend(tx3)

        # 1 gives 500 to 2 and 500 to 1
        tx4 = transaction.createTransaction(
            outputAddresses=[public2, public1],
            outputAmounts=[500, 500],
            timestamp=time.time(),
            previousTransactionHashes=[tx1.hash],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )

        self.assertTrue(chain.verifyTransactionsSyntax([tx4]))
        self.assertTrue(manager.canSpend(tx4)[0])
        manager.spend(tx4)

        # 2 gives 1500 to 3, 1 gives 500 to 3
        tx5 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[1500],
            timestamp=time.time(),
            previousTransactionHashes=[tx2.hash, tx4.hash],
            previousOutputIndices=[0, 0],
            privateKeys=[private2, private2]
        )
        self.assertTrue(manager.canSpend(tx5)[0])

        tx6 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[500],
            timestamp=time.time(),
            previousTransactionHashes=[tx4.hash],
            previousOutputIndices=[1],
            privateKeys=[private1]
        )

        self.assertTrue(manager.canSpend(tx6)[0])
        self.assertTrue(chain.verifyTransactionsSyntax([tx5, tx6]))
        manager.spend(tx5)
        manager.spend(tx6)

        # Revert the 500 transaction to 3. 3 should now have 2500,
        # 1 should now have 500.
        manager.revert(tx6)

        # Should not be able to spend 3000
        tx7 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[3000],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash, tx5.hash, tx6.hash],
            previousOutputIndices=[0, 0, 0],
            privateKeys=[private3, private3, private3]
        )
        self.assertFalse(manager.canSpend(tx7)[0])

        # Should be able to spend 2500 instead.
        tx7 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[2500],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash, tx5.hash],
            previousOutputIndices=[0, 0],
            privateKeys=[private3, private3]
        )
        self.assertTrue(manager.canSpend(tx7)[0])

        # Give the 500 back to 3 from 1.
        manager.spend(tx6)

        tx7 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[3000],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash, tx5.hash, tx6.hash],
            previousOutputIndices=[0, 0, 0],
            privateKeys=[private3, private3, private3]
        )
        self.assertTrue(manager.canSpend(tx7)[0])

        # Use invald private key
        tx7 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[3000],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[0],
            privateKeys=[private2]
        )
        self.assertFalse(manager.canSpend(tx7)[0])


class TestChain(unittest.TestCase):
    def test_createValidChain(self):
        testChain = chain.Chain()

        driver = testChain.head.transactions

        next = mine.generateNextBlock(testChain.head, driver)
        testChain.addBlock(next)
        self.assertTrue(
            testChain.head.hash == next.hash,
            msg="Test if a block can be added to a chain.")

        nextnext = mine.generateNextBlock(next, driver)
        testChain.addBlock(nextnext)
        self.assertTrue(
            testChain.head.hash == nextnext.hash,
            msg="Test if a second block can be added to a chain.")

        with self.assertRaises(chain.ChainException):
            testChain.addBlock(next)

    def test_createLongChainValid(self):
        pass
        # tx1 = transaction.createTransaction([public1], [1000], timestamp)
        # tx2 = transaction.createTransaction([public2], [1000], timestamp)
        # tx3 = transaction.createTransaction([public3], [1000], timestamp)

        # mine.ge
    #     testChain = chain.Chain()

    #     with self.assertRaises(chain.ChainException):
    #         testChain.addBlock(block.Block(1, 32, "ASDF", 0, ""))

    #     with self.assertRaises(chain.ChainException):
    #         next = mine.generateNextBlock(testChain.head, "DATA")
    #         next.data = ""  # Intentionally corrupt block
    #         testChain.addBlock(next)

#     def test_fork(self):
#         testChain = chain.Chain()

#         # Add two blocks to the chain
#         next = mine.generateNextBlock(testChain.head, "DATA")
#         nextnext = mine.generateNextBlock(next, "DATA")
#         testChain.addBlock(next)
#         testChain.addBlock(nextnext)
#         self.assertTrue(testChain.head.hash == nextnext.hash)

#         # Create a fork off the first block
#         nextFork = mine.generateNextBlock(next, "DATA")
#         testChain.addBlock(nextFork)
#         # At this point, we expect both forks to be the same length, but
#         # the first chain should take presedence.
#         self.assertTrue(testChain.head.hash == nextnext.hash)

#         # Now the fork is longer than the original chain, so the head
#         # should point to the new fork.
#         nextnextFork = mine.generateNextBlock(nextFork, "DATA")
#         testChain.addBlock(nextnextFork)
#         self.assertTrue(testChain.head.hash == nextnextFork.hash)

#     def test_forkAsList(self):
#         # Redo the previous test, except pass the nodes as a list.
#         testChain = chain.Chain()

#         # Add two blocks to the chain
#         next = mine.generateNextBlock(testChain.head, "DATA")
#         nextnext = mine.generateNextBlock(next, "DATA")
#         nextFork = mine.generateNextBlock(next, "DATA")
#         nextnextFork = mine.generateNextBlock(nextFork, "DATA")
#         blocksToAdd = [next, nextnext, nextFork, nextnextFork]
#         testChain.addBlocks(blocksToAdd)
#         self.assertTrue(testChain.head.hash == nextnextFork.hash)