import time
import unittest
from core import transaction
from Crypto.PublicKey import RSA


class TestTransaction(unittest.TestCase):
    # Pregenerate private and public keys beforehand
    # to speed up running the tests.
    private1 = RSA.generate(2048)
    public1 = private1.publickey().exportKey('DER').hex()
    private2 = RSA.generate(2048)
    public2 = private2.publickey().exportKey('DER').hex()
    private3 = RSA.generate(2048)
    public3 = private3.publickey().exportKey('DER').hex()

    def test_transactionInputValidation(self):
        privateKey = TestTransaction.private1
        publicKey = TestTransaction.public1

        """
        Simulataed transaction
        1 gets 1000 bitcoin
        1 sends 700 bitcoin to 2 and 300 bitcoin to 3
        2 sends 700 bitcoin to 3
        3 sends 1000 bitcoin to 1
        """

        firstTransaction = transaction.createTransaction(
            outputAddresses=[publicKey],
            outputAmounts=[1000],
            timestamp=time.time())

        # Create a valid input based on that first transaction
        nextTransaction = transaction.createTransaction(
            outputAddresses=[TestTransaction.public2, TestTransaction.public3],
            outputAmounts=[700, 300],
            timestamp=time.time(),
            previousTransactionHashes=[firstTransaction.hash],
            previousOutputIndices=[0],
            privateKeys=[privateKey]
        )

        self.assertTrue(
            transaction.verifyTransactionInput(
                firstTransaction, nextTransaction, 0)[0])

        transactionFrom2to3 = transaction.createTransaction(
            outputAddresses=[TestTransaction.public3],
            outputAmounts=[700],
            timestamp=time.time(),
            previousTransactionHashes=[nextTransaction.hash],
            previousOutputIndices=[0],
            privateKeys=[TestTransaction.private2]
        )

        self.assertTrue(
            transaction.verifyTransactionInput(
                nextTransaction, transactionFrom2to3, 0)[0]
        )

        finalTransaction = transaction.createTransaction(
            outputAddresses=[TestTransaction.public1],
            outputAmounts=[10000],
            timestamp=time.time(),
            previousTransactionHashes=[
                transactionFrom2to3.hash,
                nextTransaction.hash
            ],
            previousOutputIndices=[0, 1],
            privateKeys=[TestTransaction.private3, TestTransaction.private3]
        )

        self.assertTrue(
            transaction.verifyTransactionInput(
                nextTransaction, finalTransaction, 1)[0]
        )
        self.assertTrue(
            transaction.verifyTransactionInput(
                transactionFrom2to3, finalTransaction, 0)[0]
        )

        # Forger tries to create a transaction with an output that they don't
        # own the public key to.
        forgerPrivateKey = TestTransaction.private2
        forgerTransaction = transaction.createTransaction(
            outputAddresses=[publicKey],
            outputAmounts=[1000],
            timestamp=time.time(),
            previousTransactionHashes=[firstTransaction.hash],
            previousOutputIndices=[0],
            privateKeys=[forgerPrivateKey]
        )

        self.assertFalse(
            transaction.verifyTransactionInput(
                firstTransaction, forgerTransaction, 0)[0])

    def test_transactionCreation(self):
        # Invalid number of addresses for amounts
        with self.assertRaises(AssertionError):
            transaction.createTransaction(
                outputAddresses=[TestTransaction.public1,
                                 TestTransaction.public2],
                outputAmounts=[1000],
                timestamp=time.time())

        # Invalid output amount
        with self.assertRaises(AssertionError):
            transaction.createTransaction(
                outputAddresses=[TestTransaction.public1],
                outputAmounts=[0],
                timestamp=time.time())