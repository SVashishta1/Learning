"""Download and load MNIST (70,000 handwritten digits, 28x28 pixels) with numpy only.

The four original files are tried from several mirrors, in order, because any single website
can be down or blocked. Each file is checked with an MD5 "fingerprint" so a broken download
is never used. Files are saved in a `mnist_data/` folder next to this script and reused.
(This is a copy of lesson 05's mnist.py. If lesson 05 already downloaded the files, they are reused.)

Run this file on its own to download and see one digit:   python mnist.py
"""
import gzip
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np

MIRRORS = [
    "https://ossci-datasets.s3.amazonaws.com/mnist/",           # the mirror PyTorch's torchvision uses
    "https://storage.googleapis.com/cvdf-datasets/mnist/",       # Google's copy
    "https://raw.githubusercontent.com/fgnt/mnist/master/",      # a copy on GitHub
]
# file name -> MD5 fingerprint of the correct file (the same values torchvision checks)
FILES = {
    "train-images-idx3-ubyte.gz": "f68b3c2dcbeaaa9fbdd348bbdeb94873",
    "train-labels-idx1-ubyte.gz": "d53e105ee54ea40749a09fcbcd1e9432",
    "t10k-images-idx3-ubyte.gz": "9fb629c4189551a2d022fa330f9573f3",
    "t10k-labels-idx1-ubyte.gz": "ec29112dd5afa0611ce80d1b7f02629c",
}
HERE = Path(__file__).resolve().parent
LESSON_05_DATA = HERE.parent / "05-numpy-network-reads-handwriting" / "mnist_data"
if os.environ.get("MNIST_DIR"):            # you chose a folder yourself
    DATA_DIR = Path(os.environ["MNIST_DIR"])
elif LESSON_05_DATA.exists():              # reuse lesson 05's download instead of fetching 11 MB again
    DATA_DIR = LESSON_05_DATA
else:
    DATA_DIR = HERE / "mnist_data"


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def download(name):
    """Make sure DATA_DIR/name exists and is correct; try each mirror until one works."""
    path = DATA_DIR / name
    if path.exists() and md5(path) == FILES[name]:
        return path
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for mirror in MIRRORS:
        try:
            print(f"downloading {name} from {mirror} ...", flush=True)
            with urllib.request.urlopen(mirror + name, timeout=60) as response:
                path.write_bytes(response.read())
            if md5(path) == FILES[name]:
                return path
            print("  the file was damaged (wrong fingerprint), trying the next mirror")
        except OSError as err:                      # no internet, blocked, timeout...
            print(f"  failed: {err}")
    sys.exit(f"Could not download {name}. Check your internet connection, or download the 4 files "
             f"by hand (see the README) into {DATA_DIR}")


def read_images(path):
    with gzip.open(path, "rb") as f:
        data = f.read()
    # The first 16 bytes are a header: magic number, count, rows, cols (big-endian integers).
    count, rows, cols = (int.from_bytes(data[i:i + 4], "big") for i in (4, 8, 12))
    pixels = np.frombuffer(data, dtype=np.uint8, offset=16)
    return pixels.reshape(count, rows * cols)        # one row of 784 numbers (0..255) per image


def read_labels(path):
    with gzip.open(path, "rb") as f:
        data = f.read()
    return np.frombuffer(data, dtype=np.uint8, offset=8).astype(np.int64)   # 8-byte header, then one byte per label


def load_mnist():
    """Return (X_train, y_train, X_test, y_test). X values are floats from 0 (white) to 1 (black)."""
    X_train = read_images(download("train-images-idx3-ubyte.gz")).astype(np.float32) / 255.0
    y_train = read_labels(download("train-labels-idx1-ubyte.gz"))
    X_test = read_images(download("t10k-images-idx3-ubyte.gz")).astype(np.float32) / 255.0
    y_test = read_labels(download("t10k-labels-idx1-ubyte.gz"))
    return X_train, y_train, X_test, y_test


def show(image_row):
    """Print a 784-number image as 28 lines of text art."""
    shades = " .:-=+*#%@"
    for r in range(28):
        print("".join(shades[min(9, int(v * 10))] for v in image_row[r * 28:(r + 1) * 28]))


if __name__ == "__main__":
    X_train, y_train, X_test, y_test = load_mnist()
    print(f"train: {X_train.shape} images, {y_train.shape} labels | test: {X_test.shape}, {y_test.shape}")
    print(f"files are in {DATA_DIR}")
    print(f"first training label: {y_train[0]}")
    show(X_train[0])
