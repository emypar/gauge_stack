#!/usr/bin/env python3

import argparse
import json
import pickle
import sys

def normalize_reference(ref):
    return {
        t: tuple(sorted(ref[t])) for t in ref
    }

def normalize_result(res):
    norm = {}
    for target, blocks in res.items():
        if len(blocks) == 0:
            continue
        norm[int(target)] = tuple(sorted(
            int(b.replace(".", "")) for b in blocks
        ))
    return norm


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pkl_file")
    parser.add_argument("res_json_file")
    args = parser.parse_args()

    with open(args.pkl_file, 'rb') as f:
        ref = pickle.load(f)

    with open(args.res_json_file, "rt") as f:
        res = json.load(f)

    norm_ref = normalize_reference(ref)
    norm_res = normalize_result(res)

    ref_targets = set(norm_ref)
    res_targets = set(norm_res)

    missing_targets = ref_targets - res_targets
    if missing_targets:
        print("Missing targets: ", sorted(missing_targets), file=sys.stderr)
    unexpected_targets = res_targets - ref_targets
    if unexpected_targets:
        print("Unexpected targets: ", sorted(unexpected_targets), file=sys.stderr)
    
    for target in sorted(ref_targets.intersection(res_targets)):
        ref_blocks = norm_ref[target]
        res_blocks = norm_res[target]
        if ref_blocks != res_blocks:
            print(f"{target}:\n want: {ref_blocks}\n  got: {res_blocks}", file=sys.stderr)


