import unittest
import time
from core import block, transaction, mine, chain
from Crypto.PublicKey import RSA


class TestBlock(unittest.TestCase):
    private1 = RSA.generate(2048)
    public1 = private1.publickey().exportKey('DER').hex()
    private2 = RSA.generate(2048)
    public2 = private2.publickey().exportKey('DER').hex()
    private3 = RSA.generate(2048)
    public3 = private3.publickey().exportKey('DER').hex()

    def test_serialization(self):
        h = "2ac9a6746aca543af8dff39894cfe8173afba21eb01c6fae33d52947222855ef"

        public = TestBlock.public1
        private = TestBlock.private1

        t1 = transaction.createTransaction(
            outputAddresses=[public],
            outputAmounts=[700],
            timestamp=time.time(),
            previousTransactionHashes=[h],  # This is just a dummy value
            previousOutputIndices=[0],
            privateKeys=[private]
        )

        b = block.Block(32, 32, [t1], 0, h)
        serialized = b.asJSON()
        deserialized = block.createFromJSON(serialized)
        self.assertTrue(b == deserialized)

        # Corrupt t1 before serialization, make sure that it cannot be
        # deserialized.
        t1.outputs[-1].amount = 1  # Corrupt the transaction data.
        b = block.Block(32, 32, [t1], 0, h)
        serialized = b.asJSON()
        print("_____")
        with self.assertRaises(block.BlockException):
            block.createFromJSON(serialized)

    def test_genesis(self):
        genesis = block.genesisBlock()
        self.assertTrue(genesis is not None)