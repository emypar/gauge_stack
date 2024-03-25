#! /usr/bin/env python3

''' Check and report on pickle files
'''

import argparse
import pickle
import sys

from algo.validator import validate

def check_ok(pkl_file):
    with open(pkl_file, 'rb') as f:
        target_to_blocks = pickle.load(f)
    ok = True
    for target, blocks in target_to_blocks.items():
        if not validate(blocks, target):
            ok = False
    return ok

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pkl_file", nargs="+")
    args = parser.parse_args()
    for pkl_file in args.pkl_file:
        if check_ok(pkl_file):
            print(f"{pkl_file} OK")
        else:
            print(f"{pkl_file} Failed", file=sys.stderr)
