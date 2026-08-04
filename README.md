# Crystal Clear

Layered visual encryption implementation: given an image, decomposes it into frequency layers, encrypts each layer individually, so image becomes progressively clearer as more keys are supplied. 

WIT Summer 2026 COMP3590 Applied Cryptography term project. 

## Setup (mac)
```bash
git clone <repo url>
cd crystal-clear
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## Running demo (mac)
```bash
(.venv) python3 demo.py --help
(.venv) python3 demo.py path/to/image.jpg                       # defaults to AES-GCM
(.venv) python3 demo.py -aes-gcm path/to/image.jpg
(.venv) python3 demo.py -chacha20-poly1305 path/to/image.jpg
(.venv) python3 demo.py -aes-gcm-siv path/to/image.jpg out_dir  # specify output directory
```

## Running benchmark (mac)
```bash
(.venv) python3 bench.py --help
(.venv) python3 bench.py                            # default sizes, 25 repeats x 50 calls each
(.venv) python3 bench.py -n 100 -r 15               # specify number of calls, number of repeats
(.venv) python3 bench.py --sizes 16384 65536        # custom input sizes (bytes)
```