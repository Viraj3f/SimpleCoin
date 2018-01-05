import unittest
import time
from core import chain, transaction, mine
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
    def test_createLongChainValid(self):
        # Genesis has 1000 coins
        testChain = chain.Chain()
        tx1 = transaction.createTransaction([public1], [1000], time.time())
        tx2 = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[1000],
            timestamp=time.time(),
            previousTransactionHashes=[tx1.hash],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )

        # 1 has 1000 SPC
        b1 = mine.generateNextBlock(testChain.head, [tx1, tx2])
        testChain.addBlock(b1)

        # 1 gives 400 to 2 and 600 to 1
        tx3 = transaction.createTransaction(
            outputAddresses=[public2, public1],
            outputAmounts=[400, 600],
            timestamp=time.time(),
            previousTransactionHashes=[tx2.hash],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )
        b2 = mine.generateNextBlock(testChain.head, [tx3])
        testChain.addBlock(b2)

        # Test that an invalid transaction does not mess up the state
        # 2 gives 400 to 3
        tx4 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[400],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[0],
            privateKeys=[private2]
        )
        # 1 tries to give not enough money to 3
        badTx = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[10],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[1],
            privateKeys=[private1]
        )

        b3 = mine.generateNextBlock(testChain.head, [badTx, tx4])
        with self.assertRaises(chain.UTXOException):
            testChain.addBlock(b3)
        assert testChain.head == b2

        # Proper transaction. 3 should now have 400 from 2 and 600 from 1
        tx5 = transaction.createTransaction(
            outputAddresses=[public3],
            outputAmounts=[600],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[1],
            privateKeys=[private1]
        )

        b3 = mine.generateNextBlock(testChain.head, [tx5, tx4])
        testChain.addBlock(b3)
        assert testChain.head == b3

        # Create a fork off b2. It should be added to the chain.
        # 2 gives 200 to 2 and 100 to 3. This is techincally invalid.
        tx4alt = transaction.createTransaction(
            outputAddresses=[public3, public2],
            outputAmounts=[100, 200],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[0],
            privateKeys=[private2]
        )
        b3alt = mine.generateNextBlock(b2, [tx4alt])
        testChain.addBlock(b3alt)

        # 2 gives 200 to 1
        tx5alt = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[200],
            timestamp=time.time(),
            previousTransactionHashes=[tx4alt.hash],
            previousOutputIndices=[1],
            privateKeys=[private2]
        )
        b4alt = mine.generateNextBlock(b3alt, [tx5alt])
        with self.assertRaises(chain.UTXOException):
            testChain.addBlock(b4alt)

        with self.assertRaises(chain.NoParentException):
            testChain.addBlock(b4alt)

        # The fork was invalid. Try adding it again,
        # except
        tx4alt = transaction.createTransaction(
            outputAddresses=[public3, public2],
            outputAmounts=[200, 200],
            timestamp=time.time(),
            previousTransactionHashes=[tx3.hash],
            previousOutputIndices=[0],
            privateKeys=[private2]
        )
        b3alt = mine.generateNextBlock(b2, [tx4alt])
        testChain.addBlock(b3alt)

        tx5alt = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[200],
            timestamp=time.time(),
            previousTransactionHashes=[tx4alt.hash],
            previousOutputIndices=[1],
            privateKeys=[private2]
        )
        b4alt = mine.generateNextBlock(b3alt, [tx5alt])
        testChain.addBlock(b4alt)
        assert testChain.head == b4alt
