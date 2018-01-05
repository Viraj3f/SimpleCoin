# SimpleCoin

Simple blockchain-based cryptocurrency implementation inspired by [Naive Coin](https://github.com/lhartikk/naivecoin). The entire blockchain is kept in memory, but there is simple JSON persistance for use between sessions. Unlike Naive Coin, simplecoin keeps forks in the blockchain and tries to deal with them.

# Instructions
Coming soon...

# Todo
* Miner algorithims
* P2P + wallets

# Transactions
Transactions are sent from one simpleCoin address to another. A transaction consists of a list of inputs and a list of outputs. Each output contains an address (the person recieving the simpleCoin) and an amount (SPC) of simpleCoin to send. An address recieving a simpleCoin from an ouput can later spend that exact amount of simpleCoin as an input for a future transaction. An input contains a reference to a previous output transaction by its hash transaction hash and index.

Transactions contain:
* List of transaction inputs
* List of transaction outputs
* A timestamp
* A hash. A hash is helped to stay unique by using a timestamp.

Transaction Inputs contain:
* A reference to a previous transaction (by using the hash)
* An index, to associate a particular output transaction with an input
* A signature from the payee that is used to a verify a payment. The RSA signature is made using PKCS1 PSS with a SHA-256 hash of the previous transaction hash + index + output data (output addresses and amounts). The private key of the new sender (who was previously a reciever) is used to generate the digital signature. The signature is similar to SIGHASH_ALL in the bitcoin protocol.

Transaction outputs contain:
* An address to send the coin to. In simpleCoin, it is just the public key of the reciever.
* The amount of coin to send.

A transaction input is valid if:
* The referenced transaction hash matches the actual transaction hash.
* The referenced transaction is not out of bounds
* The signature of the transaction input can be verified using the the public key of the sender. The public key of the sender is the address from the referenced output.

## Coinbase Transactions
A special type of transaction occurs as a reward to miners. It is a transaction with only one output of 100 SPC to a single address. Unlike bitcoin, the reward fee is constant. This also means that there are an infinite number of SPC in existance. There are no transaction fees in simpleCoin.

## Example
```
{
  "inputs": [
    {
      "referencedHash": "d77c329d47cb31ee4e56e826120402cf90abbeee3afa79a3778124ea4910aed4",
      "referencedOutputIndex": 0,
      "signature": "979aa3924..."
    },
    {
      "referencedHash": "39ea3a21319be81e2a3ab2e2587663cef40348838dcf46cafb12c03c5f22d413",
      "referencedOutputIndex": 1,
      "signature": "a3a85b577..."
    }
  ],
  "outputs": [
    {
      "amount": 10000,
      "address": "308201223...:
    }
  ],
  "timestamp": 1515049925.2865548,
  "hash": "d42feea46f372e805952d4815b27b68293b237a041f72f11bbc6697eff0195f7"
}
```

# Blocks
A block is a list of transactions. It contains an index, timestamp, transactions, noonce (random number that when hashed demonstrates the proof of work) and it's predecessors hash.

## Proof of Work
A proof of work is required for each block if it wants to be added to the chain. The purpose of the proof of work is to prevent one single node from broadcasting fradulent blocks to other nodes. In this implementation, the proof of work is to have the first byte of the block's hash has equal to 0. This makes simpleCoin particularily vulnerable to alternative history attacks. This can be easily fixed by increasing the POW required for each block. However, the "easier" POW allows for faster testing and more time experimenting.

## Example (genesis block)
```
{
    "hash": "d4942fcc1f1cfef1653616c9da0f9710da679126e6baadc7c9eae13e3a29398c",
    "index": 0,
    "timestamp": 1514689482.0,
    "noonce": 0,
    "previousHash": "",
    "transactions": [
        {
            "inputs": [],
            "outputs": [
                {
                    "amount": 10000,
                    "address": "308201223"...
                }
            ],
            "timestamp": 1514689482.0,
            "hash": "178c0c15c4d7cba5171694109f76949fd9e003cfb70053523fae013558001e95"
        }
    ]
}
```

# Blockchain
The chain is a linked list of blocks. New blocks are added directly to the head of a chain, or forked off on the side.

A new block is considered valid when:
* The index of the block is equal to the index + 1 of the block furthest down the chain.
* The new block's hash matches the hash of the block furthest down the chain.
* The block is hashed properly.
* The block has a valid proof of work.
* There are no duplicate transaction methods.
* The list of transactions has valid syntax, which means:
    * The hash of the transaction is valid
    * There are no duplicate transactions
    * There is at most one coinbase transaction, and that amount is equal to 1000 SPC.
    * Transaction inputs don't reference the same utxos.
    * The output amounts are greater than zero.
    * The number of transactions per block not greater than 5

If a new block is valid with respect to the heado the chain, these additional checks are ran:
* The referenced input transactions are part of the internal set of unspent output transactions (UTXO)
* The transaction inputs are valid and are signed properly. (see the Transaction section)
* The sum of the referenced output amounts are equal to the sum of the amounts of the transaction output (unless it is coinbase)

In the case where a new block is valid at some point that is not the head, a new fork is created. The head is updated automatically to match head of the longest fork. When a new fork becomes the new main chain, then the forked blocks are individually validated from common ancestor.