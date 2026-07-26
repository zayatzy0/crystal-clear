"""
Shared constants, methods.
"""
import numpy as np

# DCT
BLOCK = 8                                   # process images in 8x8 pixel tiles

# frequency cutoffs
DCT_LAYER_RADII = (1, 2, 3)                 # DCT layer radii for low, mid, high frequency layers
N_LAYERS = len(DCT_LAYER_RADII) + 1         # number of DCT layers

# AEAD params
NONCE_BYTES = 12                            # number of bytes in a nonce, 96 bits, standard for AES-GCM
