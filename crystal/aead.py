"""
AEAD encryption/decryption for one layer of bytes. 

Supports three AEAD ciphers (see Phase II design doc §2.i): AES-GCM, 
ChaCha20-Poly1305, AES-GCM-SIV. 
Reference: https://cryptography.io/en/latest/hazmat/primitives/aead/ 
"""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305, AESGCMSIV
from . import config

# dict mapping <cipher-name> strings to cryptography's AEAD classes
CIPHERS = {
    "AES-GCM": AESGCM,                          # NIST SP 800-38D
    "ChaCha20-Poly1305": ChaCha20Poly1305,      # RFC 8439
    "AES-GCM-SIV": AESGCMSIV,                   # RFC 8452
}

def generate_key(cipher_name = "AES-GCM"):
    """
    Generate a random 256-bit (32-byte) key for the given cipher.

    arguments:
    cipher: cipher selection; defaults to AES-GCM if blank

    returns: 256-bit key for selected cipher
    """
    cipher = CIPHERS[cipher_name]                   # get actual cipher from CIPHERS dict
    if cipher_name == "ChaCha20-Poly1305":          # ChaCha20Poly1305.generate_key() takes no args (always 256-bit)
        return cipher.generate_key()                
    return cipher.generate_key(bit_length = 256)    # AESGCM / AESGCMSIV both require bit_length explicitly

def encrypt_layer(key, plaintext_bytes, layer_index, cipher_name = "AES-GCM"):
    """
    Encrypt layer plaintext_bytes at layer index layer_index using provided 
    key with cipher cipher_name.

    arguments:
    key: bytes (from generate_key())
    plaintext_bytes: layer's coefficients (already converted)
    layer_index: integer, 0-3
    cipher_name: cipher selection; defaults to AES-GCM if blank

    returns: (nonce, ciphertext)
    """
    cipher = CIPHERS[cipher_name]                   # get actual cipher from CIPHERS dict
    cipher_instance = cipher(key)                   # instantiate cipher object with given key
    nonce = os.urandom(config.NONCE_BYTES)          # generate a random nonce
    aad = layer_index.to_bytes(1, 'big')            # convert layer index to bytes
    ciphertext = cipher_instance.encrypt(nonce, plaintext_bytes, aad)   # ciphertext with 16-byte tag
    return nonce, ciphertext

def decrypt_layer(key, nonce, ciphertext, layer_index, cipher_name = "AES-GCM"):
    """
    Decrypt layer ciphertext at layer index layer_index instanciated with 
    key given nonce with cipher cipher_name.

    arguments:

    key: bytes (from generate_key())
    nonce: bytes (from encrypt_layer)
    ciphertext: bytes (from encrypt_layer)
    layer_index: integer, 0-3
    cipher: cipher selection; defaults to AES-GCM if blank

    returns: plaintext_bytes
    """
    cipher = CIPHERS[cipher_name]                   # get actual cipher from CIPHERS dict
    cipher_instance = cipher(key)                   # instantiate cipher object with given key
    aad = layer_index.to_bytes(1, 'big')            # convert layer index to bytes
    plaintext_bytes = cipher_instance.decrypt(nonce, ciphertext, aad)   # decrypt and verify tag
    return plaintext_bytes

