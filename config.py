"""
Shared constants, methods.
"""
import numpy as np

# DCT
BLOCK = 8                                   # process images in 8x8 pixel tiles

# frequency cutoffs
DCT_LAYER_RADII = (2, 4, 8)                 # DCT layer radii for low, mid, high frequency layers
N_LAYERS = len(DCT_LAYER_RADII) + 1         # number of DCT layers

# AEAD params
NONCE_BYTES = 12                            # number of bytes in a nonce, 96 bits, standard for AES-GCM

def build_dct_matrix(n = BLOCK):
    """
    n x n orthonormal DCT-II basis matrix. 
    k rows and m columns, where k is the frequency index and m is the pixel index.
    The DCT-II basis matrix is defined as:
        C[k, m] = sqrt(2/n) * cos(pi * (2m + 1) * k / (2n)) for k = 0, 1, ..., n-1 and m = 0, 1, ..., n-1
    The first row is scaled by sqrt(1/2) to make the basis orthonormal.

    references:
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.dct.html
    """
    k = np.arange(n).reshape(-1, 1)         # frequency index (one per row)
    m = np.arange(n).reshape(1, -1)         # pixel index (one per column)
    C = np.cos(np.pi * (2 * m + 1) * k / (2 * n))   # cosine matrix
    C *= np.sqrt(2.0 / n)                   # scale every row by sqrt(2/n) so its length is 1
    C[0, :] *= np.sqrt(0.5)                 # scale down first row so it is half the scale
    return C

DCT_MATRIX = build_dct_matrix()