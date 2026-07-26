"""
Pipes together transform.py, serialize.py, and aead.py for
image encryption/decryption.
"""
import numpy as np
from cryptography.exceptions import InvalidTag  # raised by aead.decrypyt_layer()
from . import transform, serialize, aead

def encrypt_image(image):
    """
    image: (H, W, CH) array; pixel values in [0, 255]
    returns: {shape, layers[], keys[]} (bundled for demo purposes)
    """
    shape = image.shape
    image_layers = transform.to_layers(image)       # (H, W, Ch) arrays for each layer
    keys = []                                       # one per layer
    enc_layers = []

    for i, layer_array in enumerate(image_layers):
        key = aead.generate_key()                   # generate random key for this layer
        plaintext_bytes = serialize.layer_to_bytes(layer_array)     # convert layer to bytes

        nonce, ciphertext = aead.encrypt_layer(key, plaintext_bytes, layer_index = i)   #encrypt layer
        
        keys.append(key)
        enc_layers.append({ "nonce": nonce, "ciphertext": ciphertext }) # store nonce and ciphertext for this layer
    
    return { "shape": shape, "layers": enc_layers, "keys": keys }

def decrypt_image(encrypted_image, held_keys):
    """
    encrypted_image: {shape, layers[], keys[]} (bundled for demo purposes)
    held_keys: {layer_index: key} dictionary of keys held by the user
    returns: (H, W, Ch) array; pixel values in [0, 255]
    """
    shape = encrypted_image["shape"]
    dec_layers = []

    for i, enc_layer in enumerate(encrypted_image["layers"]):
        if i not in held_keys:
            dec_layers.append(None)
            continue
        try: 
            ptext_bytes = aead.decrypt_layer(
                held_keys[i], enc_layer["nonce"], enc_layer["ciphertext"], layer_index = i
            )
            dec_layers.append(serialize.bytes_to_layer(ptext_bytes, shape))
        except InvalidTag:
            dec_layers.append(None)     # wrong key/mismatch
    
    dec_image = transform.from_layers(dec_layers, shape)
    return np.clip(dec_image, 0, 255).astype(np.uint8)     # clip because DTC inverse can overshoot
