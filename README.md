# BlockPy

Simple blockchain implementation inspired by [Naive Chain](https://github.com/lhartikk/naivechain).

# Blocks
A block is a collection of data. It contains an index, timestamp, data, noonce (random number that when hashed demonstrates the proof of work) and it's predecessors hash. This blockchain implementation does not include transactions nor a wallet.

# Proof of Work
A proof of work is required for each block if it wants to be added to the chain. The purpose of the proof of work is to prevent one single node from broadcasting fradulent blocks to other nodes. In this implementation, the proof of work is to have the first byte of the block's hash has equal to 0. Since this proof of work is relatively simple

# Chain
The chain is a linked list of blocks. New blocks are added directly to the head of a chain, or forked off on the side.

A new block is considered valid when:
* The index of the block is equal to the index + 1 of the block furthest down the chain.
* The new block's hash matches the hash of the block furthest down the chain.
* The block is hashed properly.
* The block has a valid proof of work.

If a new block is valid with respect to the head, it is added to the head of the chain. In the case where a new block is valid at some point that is not the head, a new fork is created. The head is updated automatically to match head of the longest fork.