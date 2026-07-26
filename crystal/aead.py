"""
AEAD encryption/decryption for one layer of bytes. 

Uses cryptography's AES-GCM implementation. See https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#aes-gcm for more details.
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from . import config

def generate_key():
    """
    Generate a random 256-bit (32-byte) key for AES-GCM.
    """
    return AESGCM.generate_key(bit_length = 256)

def encrypt_layer(key, plaintext_bytes, layer_index):
    """
    key = bytes (from generate_key())
    plaintext_bytes = layer's coefficients (already converted)
    layer_index = integer, 0-3

    returns: (nonce, ciphertext)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(config.NONCE_BYTES)      # generate a random nonce
    aad = layer_index.to_bytes(1, 'big')        # convert layer index to bytes
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)   # ciphertext with 16-byte tag
    return nonce, ciphertext

def decrypt_layer(key, nonce, ciphertext, layer_index):
    """
    key = bytes (from generate_key())
    nonce = bytes (from encrypt_layer)
    ciphertext = bytes (from encrypt_layer)
    layer_index = integer, 0-3

    returns: plaintext_bytes
    """
    aesgcm = AESGCM(key)
    aad = layer_index.to_bytes(1, 'big')        # convert layer index to bytes
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad)    # decrypt and verify tag
    return plaintext_bytes

