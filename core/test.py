import unittest

import block
import chain
import mine


class TestBlock(unittest.TestCase):
    def test_serializeation(self):
        h = "2ac9a6746aca543af8dff39894cfe8173afba21eb01c6fae33d52947222855ef"
        b = block.Block(32, 32, "ASDF", 0, h)
        serialized = b.json()
        deserialized = block.createFromJSON(serialized)
        self.assertTrue(b == deserialized)

        # Corrupt b before serialization, make sure that it cannot be
        # deserialized.
        b = block.Block(32, 32, "ASDF", 0, h)
        b.data = "CORRUPT"
        serialized = b.json()
        with self.assertRaises(block.BlockException):
            block.createFromJSON(serialized)

    def test_genesis(self):
        genesis = block.genesisBlock()
        self.assertTrue(genesis is not None)

    def test_createValidBlocks(self):
        genesis = block.genesisBlock()

        # Check if the first block generated is valid
        next = mine.generateNextBlock(genesis, "ASDF")
        self.assertTrue(chain.verifyNextBlock(genesis, next)[0])

        # Check the block after the first block
        nextnext = mine.generateNextBlock(next, "ASDF")
        self.assertTrue(chain.verifyNextBlock(next, nextnext))

        # Verify the second block is not valid after genesis
        self.assertFalse(chain.verifyNextBlock(genesis, nextnext)[0])

        # Generate a new block from genesis
        next2 = mine.generateNextBlock(genesis, "ASDF")
        self.assertTrue(chain.verifyNextBlock(genesis, next2)[0])

        # Verify the new genesis block does work with the old chain
        self.assertFalse(chain.verifyNextBlock(next2, nextnext)[0])

    def test_createInvalidBlocks(self):
        genesis = block.genesisBlock()

        # Make a fake block with invalid proof of work
        fake = block.Block(genesis.index + 1, 32, "ASDF", 0, genesis.hash)
        self.assertFalse(chain.verifyNextBlock(genesis, fake)[0])

        # Make a block with invalid index
        fake = block.Block(genesis.index, 32, "ASDF", 0, genesis.hash)
        self.assertFalse(chain.verifyNextBlock(genesis, fake)[0])

        # Make a block with invalid inde
        fake = block.Block(genesis.index + 1, 32, "ASDF", 0, genesis.hash)
        self.assertFalse(chain.verifyNextBlock(genesis, fake)[0])


class TestChain(unittest.TestCase):
    def test_createValidChain(self):
        testChain = chain.Chain()

        next = mine.generateNextBlock(testChain.head, "DATA")
        testChain.addBlock(next)
        self.assertTrue(
            testChain.head.hash == next.hash,
            msg="Test if a block can be added to a chain.")

        nextnext = mine.generateNextBlock(next, "DATA")
        testChain.addBlock(nextnext)
        self.assertTrue(
            testChain.head.hash == nextnext.hash,
            msg="Test if a second block can be added to a chain.")

        with self.assertRaises(chain.ChainException):
            testChain.addBlock(next)

    def test_createInvalidChain(self):
        testChain = chain.Chain()

        with self.assertRaises(chain.ChainException):
            testChain.addBlock(block.Block(1, 32, "ASDF", 0, ""))

        with self.assertRaises(chain.ChainException):
            next = mine.generateNextBlock(testChain.head, "DATA")
            next.data = ""  # Intentionally corrupt block
            testChain.addBlock(next)

    def test_fork(self):
        testChain = chain.Chain()

        # Add two blocks to the chain
        next = mine.generateNextBlock(testChain.head, "DATA")
        nextnext = mine.generateNextBlock(next, "DATA")
        testChain.addBlock(next)
        testChain.addBlock(nextnext)
        self.assertTrue(testChain.head.hash == nextnext.hash)

        # Create a fork off the first block
        nextFork = mine.generateNextBlock(next, "DATA")
        testChain.addBlock(nextFork)
        # At this point, we expect both forks to be the same length, but
        # the first chain should take presedence.
        self.assertTrue(testChain.head.hash == nextnext.hash)

        # Now the fork is longer than the original chain, so the head
        # should point to the new fork.
        nextnextFork = mine.generateNextBlock(nextFork, "DATA")
        testChain.addBlock(nextnextFork)
        self.assertTrue(testChain.head.hash == nextnextFork.hash)

    def test_forkAsList(self):
        # Redo the previous test, except pass the nodes as a list.
        testChain = chain.Chain()

        # Add two blocks to the chain
        next = mine.generateNextBlock(testChain.head, "DATA")
        nextnext = mine.generateNextBlock(next, "DATA")
        nextFork = mine.generateNextBlock(next, "DATA")
        nextnextFork = mine.generateNextBlock(nextFork, "DATA")
        blocksToAdd = [next, nextnext, nextFork, nextnextFork]
        testChain.addBlocks(blocksToAdd)
        self.assertTrue(testChain.head.hash == nextnextFork.hash)


if __name__ == '__main__':
    unittest.main()
