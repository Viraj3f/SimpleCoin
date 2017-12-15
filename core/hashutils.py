import hashlib

hashBits = 32
difficulty = 1  # Number of most significant bytes that are zero.


def hasProofOfWork(hash: str) -> bool:
    """
    Checks if the first n half-bytes in the hash are zero, where n
    is the difficulty.
    """
    return int(hash[:difficulty], 16) == 0


def generateHash(
        index: int,
        timestamp: float,
        data: str,
        noonce: int,
        previousHash: str) -> str:
    """
    Generates a SHA256 hash for the given data inside a block.
    """
    sha256Hasher = hashlib.sha256
    # Serialize the block's data by encoding it using utf8.
    serialized = \
        "{}{}{}{}".format(index, timestamp, data, noonce, previousHash) \
        .encode()
    return sha256Hasher(serialized).digest().hex()
