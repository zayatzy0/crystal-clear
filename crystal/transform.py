"""
Convert image into frequency layers, via block DCT.

Block split/reassemble adapted from pythontutorials.net's 
"How do I apply a DCT to an image in Python?" tutorial. Their example
uses the cv2.dct() function, but I am using scipy.fft.dct() as it is more
lightweight and does not require OpenCV. 

References:
https://www.pythontutorials.net/blog/how-do-i-apply-a-dct-to-an-image-in-python/
https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.dct.html

"""
import numpy as np

from scipy.fft import dct, idct
from . import config

LEVEL_SHIFT = 128.0     # center pixel values on 0 before DCT

def build_band_map(n = config.BLOCK, radii = config.DCT_LAYER_RADII):
    """
    {n}x{n} grid; each cell holds which layer that coefficient position belongs to.
    """
    bands = np.zeros((n, n), dtype=int)

    for u in range(n):              # row
        for v in range(n):          # column
            r = u + v
            band = len(radii)
            for i, cutoff in enumerate(radii):      # sort by cutoff, assign band
                if r < cutoff:
                    band = i
                    break
            bands[u, v] = band
    return bands

BAND_MAP = build_band_map()

def _dct2(block):
    """
    2D DCT of an n x n block.
    """
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def _idct2(block):
    """
    2D inverse DCT of an n x n block.
    """
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

def _to_blocks(plane):
    """
    (H, W) -> (n_blocks_h, n_blocks_w, config.BLOCK, config.BLOCK)
    Reshape and swapax pattern. 
    Adapted from pythontutorials.net's "How do I apply a DCT to an image in Python?"
    split_into_blocks() function. See their tutorial for more details:
    https://www.pythontutorials.net/blog/how-do-i-apply-a-dct-to-an-image-in-python/
    """
    H, W = plane.shape
    B  = config.BLOCK 

    return plane.reshape(H // B, B, W // B, B).swapaxes(1, 2)   # reshape to (n_blocks_h, B, n_blocks_w, B) 
                                                                #  then swap axes to (n_blocks_h, n_blocks_w, B, B)

def _from_blocks(blocks, shape):
    """
    Inverse of _to_blocks. (n_blocks_h, n_blocks_w, config.BLOCK, config.BLOCK) -> (H, W)
    Adapted from pythontutorials.net's "How do I apply a DCT to an image in Python?"
    reconstruct_image() function. See their tutorial for more details:  
    https://www.pythontutorials.net/blog/how-do-i-apply-a-dct-to-an-image-in-python/
    """
    return blocks.swapaxes(1, 2).reshape(shape)     # reshape to (n_blocks_h, B, n_blocks_w, B) 
                                                    #  then swap axes to (n_blocks_h, n_blocks_w, B, B) 
                                                    #  and reshape to (H, W)

def _block_transform(plane, fn):
    """
    Apply a function to each n x n block of the plane.
    """
    blocks = _to_blocks(plane)
    out = np.zeros_like(blocks)             # initialize output array

    for i in range(blocks.shape[0]):
        for j in range(blocks.shape[1]):
            out[i, j] = fn(blocks[i, j])    # apply function to each block
    return _from_blocks(out, plane.shape)

def to_layers(image):
    img = image.astype(np.float64) - LEVEL_SHIFT        # center pixel values on 0
    H, W, Ch = img.shape                                # H = height, W = width, Ch = channels

    transformed_channels = []
    for c in range(Ch):
        single_channel = img[:, :, c]                           # extract single channel
        transformed = _block_transform(single_channel, _dct2)   # apply DCT to each block    
        transformed_channels.append(transformed)
    coeffs = np.stack(transformed_channels, axis = -1)          # stack channels back together

    # tile band map to match image size
    tiled_bands = np.tile(BAND_MAP, (H // config.BLOCK, W // config.BLOCK))                     
    
    # for each layer, mask coeffs to keep only pixels in that band (rest zeroed), returning one (H, W, Ch) array per layer
    layers = []
    for k in range(config.N_LAYERS):
        bool_mask = (tiled_bands == k)          # true if pixed belongs to layer k
        bool_mask_3d = bool_mask[:, :, None]    # add channel dimension
        layer_k = coeffs * bool_mask_3d         # zero out coefficients not in layer k
        layers.append(layer_k)
    return layers

def from_layers(layers, shape):
    total = np.zeros(shape, dtype = np.float64)         # initialize output array
    for layer in layers:
        if layer is not None:
            total += layer                              # sum layers together
    
    H, W, Ch = shape            # H = height, W = width, Ch = channels
    
    planes = []
    for c in range(Ch):
        single_channel = total[:, :, c]                 # extract single channel as 2D (H, W) slice
        reconstructed = _block_transform(single_channel, _idct2)    # apply inverse DCT to each block
        planes.append(reconstructed)

    return np.stack(planes, axis = -1) + LEVEL_SHIFT    # stack channels back together and shift pixel values back to [0, 255]
