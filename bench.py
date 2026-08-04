"""
eBACS-style AEAD cipher benchmark for Crystal.

Runs each cipher's encrypt/decrypt many times, at a few input sizes matching
real DCT layer byte-lengths, using timeit for precision. Reports MEDIAN (per 
eBACS methodology) plus variance across repeats, in MiB/s.

NOTE: bench_one: encrypt generates a fresh key inside every timed call (matching
pipeline.py's per-layer key generation), and decrypt cycles through a pool of
distinct pre-generated (key, nonce, ciphertext) triples. 
The pool is built in a separate, UNTIMED pass before decrypt timing starts.

Usage:
    python bench.py                         # default sizes, 25 repeats x 50 calls each
    python bench.py -n 100 -r 15            # specify numer of calls, number of repeats
    python bench.py --sizes 16384 65536     # specify input sizes (bytes)
"""
import argparse
import itertools
import os
import statistics
import timeit

from crystal.aead import CIPHERS, generate_key, encrypt_layer, decrypt_layer

MiB = 1024 * 1024

# chosen to bracket real DCT layer coefficient byte count
DEFAULT_SIZES = [16 * 1024, 64 * 1024, 256 * 1024, 1024 * 1024]
# maximum size for decrypt entry pool, large enough to overload L2/L3 cache so results are not skewed
MAX_POOL_SIZE = 1000

def parse_args():
    parser = argparse.ArgumentParser(
        description = "Benchmark AES-GCM | ChaCha20-Poly1305 | AES-GCM-SIV "
                       "encrypt+decrypt throughput at several input sizes."
    )
    parser.add_argument(
        "--sizes", type = int, nargs = "+", default = DEFAULT_SIZES,
        help = f"Input sizes in bytes to test (default: {DEFAULT_SIZES})"
    )
    parser.add_argument(
        "-n", "--number", type = int, default = 50,
        help = "Calls per timing measurement (default: 50)"
    )
    parser.add_argument(
        "-r", "--repeat", type = int, default = 25,
        help = "Number of repeated measurements per size/cipher/op (default: 25)"
    )
    return parser.parse_args()

def bench_one(cipher_name, size_bytes, number, repeat):
    """
    Times encrypt and decrypt for one (cipher, size) pair.
    Returns a dict with median + variance MiB/s for each operation.

    DEVIATION FROM STANDARD eBACS METHODOLOGY, DELIBERATE:
    Typical eBACS-style AEAD benchmarks generate one key and reuse it across
    all timed calls, since key generation is usually a fixed setup cost
    amortized over many messages. 
    Crystal's pipeline.py's encrypt_image() generates a new key for every layer, 
    every time an image is encrypted, so a realistic per-layer encrypt cost 
    should include key generation. 
    Decrypt cycles through a pool of distinct pre-generated (key, nonce, ciphertext) triples. 
    The pool is built in a separate, UNTIMED pass before decrypt timing starts.

    ROUND TRIP is derived from encrypt/decrypt call medians. Previous separate implementation
    was unstable at high payload sizes due to read/write timing.
    """
    layer_index = 0                                 # fixed AAD for benchmarking; doesn't affect speed
    total_calls = number * repeat                   # number of decrypt calls timeit makes
    pool_size = min(total_calls, MAX_POOL_SIZE)     # never build more than MAX_POOL_SIZE

    # pre-built pool of distincs random plaintext to encrypt
    plaintext_pool = [ os.urandom(size_bytes) for _ in range(pool_size) ]
    plaintext_cycle = itertools.cycle(plaintext_pool)   # wraps back to entry 0 after the last one

    # pre-build a pool of distinct (key, nonce, ciphertext) triples for decrypt to cycle through (not timed)
    def make_cipher_pool_entry(plaintext):
        key = generate_key(cipher_name)
        nonce, ciphertext = encrypt_layer(key, plaintext, layer_index, cipher_name = cipher_name)
        return key, nonce, ciphertext
    cipher_pool = [ make_cipher_pool_entry(pt) for pt in plaintext_pool ]
    cipher_cycle = itertools.cycle(cipher_pool)    # wraps back to entry 0 after the last one

    def do_encrypt():
        key = generate_key(cipher_name)             # new key every call; matches real per-layer usage
        plaintext = next(plaintext_cycle)           # using plaintext pool
        return encrypt_layer(key, plaintext, layer_index, cipher_name = cipher_name)
    enc_times = timeit.repeat(do_encrypt, number = number, repeat = repeat)
    enc_mib_s = [ (size_bytes / MiB) / (t / number) for t in enc_times ]        # seconds/call -> MiB/s

    def do_decrypt():
        key, nonce, ciphertext = next(cipher_cycle)
        return decrypt_layer(key, nonce, ciphertext, layer_index, cipher_name = cipher_name)
    dec_times = timeit.repeat(do_decrypt, number = number, repeat = repeat)
    dec_mib_s = [ (size_bytes / MiB) / (t / number) for t in dec_times ]

    encrypt_median = statistics.median(enc_mib_s)
    decrypt_median = statistics.median(dec_mib_s)
    encrypt_seconds_per_mib = 1 / encrypt_median             # time to process 1 MiB via encrypt
    decrypt_seconds_per_mib = 1 / decrypt_median             # time to process 1 MiB via decrypt
    round_trip_seconds_per_mib = encrypt_seconds_per_mib + decrypt_seconds_per_mib   # total time per MiB, both steps
    round_trip_median = 1 / round_trip_seconds_per_mib       # invert back into a MiB/s figure

    return {
        "encrypt_median": encrypt_median,
        "encrypt_variance": statistics.variance(enc_mib_s),  
        "decrypt_median": decrypt_median,
        "decrypt_variance": statistics.variance(dec_mib_s),
        "round_trip_median": round_trip_median,
    }

def main():
    args = parse_args()
    results = []                                    # flat list of result rows

    for size_bytes in args.sizes:
        for cipher_name in CIPHERS:                 # preserves insertion order (AES-GCM -> ChaCha20 -> AES-GCM-SIV)
            print(f"benchmarking {cipher_name} @ {size_bytes // 1024}KB "
                  f"({args.repeat} repeats x {args.number} calls)...")
            stats = bench_one(cipher_name, size_bytes, args.number, args.repeat)
            results.append({ "cipher": cipher_name, "size_bytes": size_bytes, **stats })

    # summary table
    print()
    header = (
        f"{'cipher':<20}{'size':>8}{'enc MiB/s':>13}{'enc var':>12}"
        f"{'dec MiB/s':>13}{'dec var':>12}{'round trip MiB/s':>19}"
    )
    print(header)
    print("-" * len(header))
    prev_size = None
    for row in results:
        if prev_size is not None and row["size_bytes"] != prev_size:
            print("-" * len(header))                # separator whenever the input size changes
        prev_size = row["size_bytes"]

        size_label = f"{row['size_bytes'] // 1024}KB"
        print(
            f"{row['cipher']:<20}{size_label:>8}"
            f"{row['encrypt_median']:>13.1f}"
            f"{row['encrypt_variance']:>12.2f}"
            f"{row['decrypt_median']:>13.1f}"
            f"{row['decrypt_variance']:>12.2f}"
            f"{row['round_trip_median']:>19.1f}"
        )

if __name__ == "__main__":
    main()