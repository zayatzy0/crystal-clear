"""
Pipes together transform.py, serialize.py, and aead.py for
image encryption/decryption.
"""
import numpy as np

from cryptography.exceptions import InvalidTag  # raised by aead.decrypyt_layer()
from . import transform, serialize, aead

def encrypt_image(image, cipher_name = "AES-GCM"):
    """
    Split image pixel array into 4 layers and encrypt each layer with cipher cipher_name.

    arguments: 
    image: (H, W, CH) array; pixel values in [0, 255]
    cipher_name: cipher selection; defaults to AES-GCM if blank

    returns: {shape, layers[], keys[], cipher_name} (bundled for demo purposes)
    """
    shape = image.shape                             # tuple containing image dimensions (H, W, Ch)
    image_layers = transform.to_layers(image)       # (H, W, Ch) arrays for each layer
    keys = []                                       # one per layer
    enc_layers = []

    for i, layer_array in enumerate(image_layers):
        key = aead.generate_key(cipher_name)                        # generate random key for this layer
        plaintext_bytes = serialize.layer_to_bytes(layer_array)     # convert layer to bytes

        nonce, ciphertext = aead.encrypt_layer(                     # encrypt layer
            key, plaintext_bytes, layer_index = i, cipher_name = cipher_name
        )   
        keys.append(key)
        enc_layers.append({ "nonce": nonce, "ciphertext": ciphertext })     # store nonce and ciphertext for this layer
    
    return { "shape": shape, "layers": enc_layers, "keys": keys, "cipher_name": cipher_name }

def decrypt_image(encrypted_image, held_keys):
    """
    encrypted_image: {shape, layers[], keys[]} (bundled for demo purposes)
    held_keys: {layer_index: key} dictionary of keys held by the user
    returns: (H, W, Ch) array; pixel values in [0, 255]
    """
    shape = encrypted_image["shape"]
    cipher_name = encrypted_image.get("cipher_name", "AES-GCM")             # default just in case
    dec_layers = []

    for i, enc_layer in enumerate(encrypted_image["layers"]):
        if i not in held_keys:
            dec_layers.append(None)
            continue
        try: 
            ptext_bytes = aead.decrypt_layer(
                held_keys[i], enc_layer["nonce"], enc_layer["ciphertext"], 
                layer_index = i, cipher_name = cipher_name
            )
            dec_layers.append(serialize.bytes_to_layer(ptext_bytes, shape))
        except InvalidTag:
            dec_layers.append(None)         # wrong key/mismatch
    
    dec_image = transform.from_layers(dec_layers, shape)
    return np.clip(dec_image, 0, 255).astype(np.uint8)              # clip because DTC inverse can overshoot
