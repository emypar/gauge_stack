#! /usr/bin/env python3

''' Merge pickle files by keeping the best resolution
'''

import argparse
import pickle

from algo.validator import cmp_blocks, normalize_blocks

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--out-file",
        default="best.pkl",
        help="Output file, default: %(default)s",
    )
    parser.add_argument("pkl_file", nargs="+")
    args = parser.parse_args()

    best = {}

    for pkl_file in args.pkl_file:
        with open(pkl_file, 'rb') as f:
            target_to_blocks = pickle.load(f)
        for target, blocks in target_to_blocks.items():
            if target not in best or cmp_blocks(blocks, best[target]) > 0:
                best[target] = normalize_blocks(blocks)
    
    with open(args.out_file, "wb") as f:
        pickle.dump(best, f)

