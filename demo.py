"""
Progressive reveal demo. 

Loads real image, separates it into 4 layers using DCT, encrypts each 
of those layers using AES-GCM (different keys for each layer), then 
progressively decrypts, capturing visual output for each step. 

Usage: 
    python demo.py path/to/image.jpg
    python demo.py path/to/image.jpg out_dir    # specify output directory
"""
import os 
import sys
import numpy as np
from PIL import Image
from crystal.pipeline import encrypt_image, decrypt_image
from crystal.config import BLOCK, N_LAYERS

def load_img(path):
    """
    Load, crop image so dimensions are miltiples of BLOCK. 
    Convert image to pixel array. 
    """
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype = np.float64)
    H, W, _ = arr.shape
    H_crop = (H // BLOCK) * BLOCK
    W_crop = (W // BLOCK) * BLOCK
    return arr[:H_crop, :W_crop, :]

def save_img(img_arr, path):
    """
    Convert pixel array to PNG file.
    """
    Image.fromarray(img_arr).save(path)

def main(img_path, out_dir = "demo"):
    os.makedirs(out_dir, exist_ok = True)
    img = load_img(img_path)

    enc_bundle = encrypt_image(img)
    print(
        f"Encrypted {os.path.basename(img_path)}: "
        f"{img.shape[1]}x{img.shape[0]}, {N_LAYERS} layers"
    )

    for n in range(N_LAYERS + 1):
        held_keys = {i: enc_bundle["keys"][i] for i in range(n)}
        out = decrypt_image(enc_bundle, held_keys)
        out_path = os.path.join(out_dir, f"{n}keys.png")
        save_img(out, out_path)
        print(f"    {n} key(s) -> {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python demo.py path/to/image.jpg [out_dir]")
    main(*sys.argv[1:3])



