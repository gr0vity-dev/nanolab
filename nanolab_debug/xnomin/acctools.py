import base64
import hashlib


# this function expects account to be a 32 byte bytearray
def to_account_addr(account: bytes, prefix: str = 'nano_') -> str:
    assert (len(account) == 32)

    RFC_3548 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    ENCODING = b"13456789abcdefghijkmnopqrstuwxyz"

    h = hashlib.blake2b(digest_size=5)
    h.update(account)
    checksum = h.digest()

    # prefix account to make it even length for base32, add checksum in reverse byte order
    account2 = b'\x00\x00\x00' + account + checksum[::-1]

    # use the optimized base32 lib to speed this up
    encode_account = base64.b32encode(account2)

    # simply translate the result from RFC3548 to Nano's encoding, snip off the leading useless bytes
    encode_account = encode_account.translate(
        bytes.maketrans(RFC_3548, ENCODING))[4:]

    # add prefix, label and return
    return prefix + encode_account.decode()


def account_key(account: str) -> bytes:
    """Get the public key for account
    :param str account: account name e.g. nano_31fr1qtbrfnujcspx5xq61uxgjf9j6rzckdj1kdn61y3h53nxr7911dzetk3
    :return: 32 byte public key
    :rtype: bytes
    :raise AssertionError: for invalid account
    """
    account_prefix = "nano_"
    _B32 = b"13456789abcdefghijkmnopqrstuwxyz"
    assert (len(account) == len(account_prefix) + 60
            and account[:len(account_prefix)] == account_prefix)

    account = b"1111" + account[-60:].encode()
    account = account.translate(bytes.maketrans(_B32, base64._b32alphabet))
    key = base64.b32decode(account)

    checksum = key[:-6:-1]
    key = key[3:-5]

    assert hashlib.blake2b(key, digest_size=5).digest() == checksum

    return key