from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Example key; in production, manage securely
AES_KEY = b'\x02' * 16

def encrypt_data(data_words, key=AES_KEY):
    """
    Encrypt a list of integers (4-byte each) using AES-CTR.
    Returns nonce||ciphertext blob.
    """
    # Serialize words to bytes
    pt = b''.join(int(x).to_bytes(4, 'big', signed=False) for x in data_words)
    nonce = get_random_bytes(8)
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    ct = cipher.encrypt(pt)
    return nonce + ct

def decrypt_data(blob, key=AES_KEY):
    """
    Decrypt a blob produced by encrypt_data, returning list of integers.
    """
    nonce = blob[:8]
    ct = blob[8:]
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    pt = cipher.decrypt(ct)
    # Deserialize bytes to integers
    return [int.from_bytes(pt[i:i+4], 'big', signed=False) for i in range(0, len(pt), 4)]