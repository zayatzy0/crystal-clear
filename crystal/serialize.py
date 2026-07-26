"""
Converts numpy arrays to bytes for encryption/decryption in aead.py.
Uses numpy's built-in tobytes() and frombuffer() methods.

Reference:
https://numpy.org/doc/stable/reference/generated/numpy.ndarray.tobytes.html
"""
import numpy as np

DTYPE = np.float64

def layer_to_bytes(layer_array):
    """
    (H, W, Ch) float array -> raw bytes
    Shape not stored (needs to be provided by caller to reverse)
    """
    return layer_array.astype(DTYPE).tobytes()

def bytes_to_layer(raw_bytes, shape):
    """
    Inverse of layer_to_bytes. 
    raw bytes -> (H, W, Ch) float array
    """
    flat_array = np.frombuffer(raw_bytes, dtype=DTYPE)  # convert bytes to 1D float array
    return flat_array.reshape(shape)                    # reshape to original shape (H, W, Ch)