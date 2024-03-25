#! /usr/bin/env python3

''' Convert pickle file to bitmap for lookup
'''

import argparse
import os
import pickle
import sys

from algo import blockset_81

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--meta-file",
        help="""Metdata file, default: blockset_81.meta, under the same location
             as the .bmp.""",
    )  
    parser.add_argument(
        "-o", "--bitmap-file",
        default="blockset_81.bmp",
        help="Bitmap file, default: %(default)s",
    )
    parser.add_argument("pkl_file")
    args = parser.parse_args()

    bitmap_file = args.bitmap_file
    meta_file = args.meta_file
    if meta_file is None:
        meta_file = os.path.join(os.path.dirname(bitmap_file), "blockset_81.meta")

    # Ensure that the blockset is sorted, build the value -> index map, and the
    # label list:
    blockset_81 = sorted(blockset_81)
    labels = [f"{b/10000:.04f}" for b in blockset_81]
    max_label_sz = max(len(label) for label in labels)
    label_index_map = {b: i for i, b in enumerate(blockset_81)}
    # Find the necessary size of the bitmap in bytes:
    num_bytes = (len(blockset_81) + 7) // 8

    # Load pickle file and check its min target:
    with open(args.pkl_file, 'rb') as f:
        target_to_blocks = pickle.load(f)
    targets = sorted(target_to_blocks)
    if len(targets) == 0:
        print("Empty pickle file", file=sys.stderr)
        exit(1)
    min_target, max_target = targets[0], targets[-1]

    # Convert pickle to bitmap file:
    zeromap = bytes([0] * num_bytes)
    n_bytes = 0
    with open(bitmap_file, 'wb') as f:
        prev_target = min_target
        for target in targets:
            for _ in range(prev_target+1, target):
                n_bytes += f.write(zeromap)
            bitmap = bytearray(num_bytes)
            for block in target_to_blocks[target]:
                index = label_index_map[block]
                bitmap[index >> 3] |= 1 << (index & 7)
            n_bytes += f.write(bitmap)
            prev_target = target
    # Generate metadata file:
    with open(meta_file, "wt") as f:
        print(len(blockset_81), max_label_sz, num_bytes, min_target, max_target, file=f)
        for label in labels:
            print(label, file=f)

    print(
        "\n"
        f"Bitmap file:   {bitmap_file}, target#={len(targets)}, size={n_bytes} bytes\n"
        f"Metadata file: {meta_file}\n"
        , file=sys.stderr
    )

