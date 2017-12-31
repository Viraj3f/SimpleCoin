from typing import List, Tuple
import json

from Crypto.Signature import PKCS1_PSS
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


class TransactionInput:
    def __init__(
            self,
            previousTransactionHash: str,
            previousTransactionIndex: int,
            signature: str) -> None:
        self.referencedHash = previousTransactionHash
        self.referencedOutputIndex = previousTransactionIndex
        self.signature = signature

    def serialize(self) -> str:
        return "{}{}{}".format(
            self.referencedHash,
            self.referencedOutputIndex,
            self.signature
        )

    @staticmethod
    def serializeMultiple(inputs: List["TransactionInput"]):
        return " ".join([tInput.serialize() for tInput in inputs])

    @staticmethod
    def createSignatureHash(
            previousTransactionHash: str,
            outputIndex: int,
            outputData: str) -> SHA256.SHA256Hash:
        """
        Create a transaction signature hash for the signature
        """
        hash = SHA256.new("{}{}".format(
            previousTransactionHash,
            outputIndex,
            outputData
        ).encode('utf-8'))
        return hash
print("i love you, i think you're the best <3 i'll love you forever and I think you're the perfect man for me. I want to take a shower but someone is in the bathroom. Did you know that bathroom is used more in the United states of america versus canada which is washroom. Never ever say we both became fat please speak for yourself fah hairflip fingersnap eye roll butt twerk. anyways i really love you so much and I dont think i'll be so happy without you. you make my day every morning when i wake up and make my day again when i go to bed. Also your mom is great cause she feeds me a lot. I also really love your family because they're so nice. Anyways, just remember I love you more than I love my fried chicken. I've known you for 8 years now and we've been dating for more than 4. Never thought anybody would be more important to me than my Loblaws honey garlic chicken. I love you.")
    @staticmethod
    def createSignature(
            previousTransactionHash: str,
            outputIndex: int,
            outputData: str,
            privateKey: RSA._RSAobj) -> str:
        """
        Create a transaction signature
        """
        sigHash = TransactionInput.createSignatureHash(
            previousTransactionHash,
            outputIndex,
            outputData
        )
        signer = PKCS1_PSS.new(privateKey)
        signature = signer.sign(sigHash).hex()
        return signature


class TransactionOutput:
    def __init__(
            self,
            amount: int,
            address: str) -> None:
        self.amount = amount
        self.address = address

    @staticmethod
    def serializeMultiple(outputs: List["TransactionOutput"]):
        return " ".join([tOutput.serialize() for tOutput in outputs])

    def serialize(self) -> str:
        return "{}{}".format(
            self.amount,
            self.address,
        )


class Transaction(object):
    def __init__(
            self,
            inputs: List[TransactionInput],
            outputs: List[TransactionOutput],
            timestamp: float) -> None:
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp
        self.hash = Transaction.createHash(inputs, outputs, timestamp)

    @staticmethod
    def createHash(
            inputs: List[TransactionInput],
            outputs: List[TransactionOutput],
            timestamp: float) -> str:
        """
        Get the hash of a transaction given the inputs, oututs and timestamps.
        """
        serialized = " ".join([tInput.serialize() for tInput in inputs])
        serialized += "-"
        serialized += " ".join([tOutput.serialize() for tOutput in outputs])
        serialized += "-"
        serialized += str(timestamp)
        return SHA256.new(serialized.encode("utf_8")).hexdigest()

    def __repr__(self) -> str:
        s = {"inputs": [], "outputs": [], "timestamp": self.timestamp}

        for input in self.inputs:
            s["inputs"].append(input.__dict__)  # type: ignore

        for outputs in self.outputs:
            s["outputs"].append(outputs.__dict__)  # type: ignore

        return json.dumps(s, indent=2)


def verifyTransactionInput(
        referencedTransaction: Transaction,
        transaction: Transaction,
        inputIndex: int) -> Tuple[bool, str]:
    """
    Verifies that a transaction input referencs a valid transaction output
    with corresponding index. Also checks if the transaction input is properly
    signed.

    This method is to verify that a person using a transaction input
    is the same person who recieved it as an output.
    """
    newInput = transaction.inputs[inputIndex]
    serializedOutputs = \
        TransactionOutput.serializeMultiple(transaction.outputs)

    # Check if referenced index is out of bounds
    index = newInput.referencedOutputIndex
    if index >= len(referencedTransaction.outputs) or index < 0:
        return False, "Referenced output index is out of bound"

    if referencedTransaction.hash != newInput.referencedHash:
        return False, "Referenced transaction hash does not match."

    referencedOutput = referencedTransaction.outputs[index]
    publicKey = RSA.importKey(bytes.fromhex(referencedOutput.address))
    verifier = PKCS1_PSS.new(publicKey)
    hash = TransactionInput.createSignatureHash(
        newInput.referencedHash,
        newInput.referencedOutputIndex,
        serializedOutputs
    )
    signature = bytes.fromhex(newInput.signature)

    if not verifier.verify(hash, signature):
        return False, "Signature not valid"

    return True, ""


def createTransaction(
        outputAddresses: List[str],
        outputAmounts: List[int],
        timestamp: float,
        previousTransactionHashes: List[str] = [],
        previousOutputIndices: List[int] = [],
        privateKeys: List[RSA._RSAobj] = []) -> Transaction:
    """
    Creates a transaction object. For transactions that have no inputs
    but one or more outputs are essentially coinbase transactions.
    """
    # Check that the previous transaction hashes, indices and private
    # keys are equal
    assert len(previousTransactionHashes) == len(previousOutputIndices)
    assert len(previousOutputIndices) == len(privateKeys)
    assert len(previousOutputIndices) >= 0

    # Do the same for the output addresses and output amounts.
    assert len(outputAddresses) == len(outputAmounts)
    assert len(outputAmounts) > 0

    outputs = []
    for i in range(len(outputAddresses)):
        amount = outputAmounts[i]
        assert amount > 0
        outputs.append(TransactionOutput(amount, outputAddresses[i]))

    inputs = []
    outputData = TransactionOutput.serializeMultiple(outputs)
    for i in range(len(previousTransactionHashes)):
        signature = TransactionInput.createSignature(
            previousTransactionHashes[i],
            previousOutputIndices[i],
            outputData,
            privateKeys[i])

        inputs.append(TransactionInput(
            previousTransactionHashes[i],
            previousOutputIndices[i],
            signature
        ))

    return Transaction(inputs, outputs, timestamp)
