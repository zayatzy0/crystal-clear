"""
Progressive reveal demo. 

Loads real image, separates it into 4 layers using DCT, encrypts each 
of those layers using the chosen AEAD cipher (different keys for each layer), 
then progressively decrypts, capturing visual output for each step. 

Usage: 
    python demo.py path/to/image.jpg                        # no flag -> defaults to AES-GCM
    python demo.py -aes-gcm path/to/image.jpg
    python demo.py -chacha20-poly1305 path/to/image.jpg
    python demo.py -aes-gcm-siv path/to/image.jpg out_dir   # specify output directory
    python demo.py --help
"""
import argparse
import os 
import sys
import numpy as np
from PIL import Image
from crystal.pipeline import encrypt_image, decrypt_image
from crystal.config import BLOCK, N_LAYERS

def parse_args():
    """
    CLI builder. 

    Cipher choice (optional): [-aes-gcm | -chacha20-poly1305 | -aes-gcm-siv]; defaults to aes-gcm
    """
    parser = argparse.ArgumentParser(
        prog = "demo.py",
        description = "Crystal progressive-reveal demo: splits an image into DCT "
                       "frequency layers, encrypts each with independent keys, "
                       "then decrypts progressively (0 keys -> all keys).",
        epilog = "example: python demo.py -aes-gcm path/to/image.jpg out_dir",
    )

    cipher_group = parser.add_mutually_exclusive_group()        # optional; default = AES-GCM
    cipher_group.add_argument(
        "-aes-gcm", dest = "cipher", action = "store_const", const = "AES-GCM",
        help = "Encrypt layers with AES-GCM (NIST SP 800-38D) [default]"
    )
    cipher_group.add_argument(
        "-chacha20-poly1305", dest = "cipher", action = "store_const", const = "ChaCha20-Poly1305",
        help = "Encrypt layers with ChaCha20-Poly1305 (RFC 8439)"
    )
    cipher_group.add_argument(
        "-aes-gcm-siv", dest = "cipher", action = "store_const", const = "AES-GCM-SIV",
        help = "Encrypt layers with AES-GCM-SIV (RFC 8452)"
    )
    parser.set_defaults(cipher = "AES-GCM")   

    parser.add_argument("image_path", help = "Path to the input image (jpg/png/etc)")
    parser.add_argument(
        "out_dir", nargs = "?", default = "demo",
        help = "Directory to write progressive-reveal PNGs into (default: demo)"
    )

    return parser.parse_args()

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

def main(img_path, cipher_name, out_dir = "demo"):
    os.makedirs(out_dir, exist_ok = True)
    img = load_img(img_path)

    enc_bundle = encrypt_image(img, cipher_name = cipher_name)
    print(
        f"Encrypted {os.path.basename(img_path)} with {cipher_name}: "
        f"{img.shape[1]}x{img.shape[0]}, {N_LAYERS} layers"
    )

    for n in range(N_LAYERS + 1):
        held_keys = {i: enc_bundle["keys"][i] for i in range(n)}
        out = decrypt_image(enc_bundle, held_keys)
        out_path = os.path.join(out_dir, f"{n}keys.png")
        save_img(out, out_path)
        print(f"    {n} key(s) -> {out_path}")

if __name__ == "__main__":
    args = parse_args()   
    main(args.image_path, args.cipher, args.out_dir)



