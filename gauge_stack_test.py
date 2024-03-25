#!/usr/bin/env python3

import argparse
import pickle
import sys

from algo import (
    blockset_81, 
    min_target,
    max_target,
    gofai,
    greedy,
)

from algo.validator import validate, normalize_blocks

resolvers = {
    "gofai": gofai.resolve,
    "greedy": greedy.resolve,
}

def test_range(start, end, resolver):
    ok = True
    range_list = []
    range_start = None
    for target in range(start, end+1):
        if target % 1000 == 0:
            print(f"Trying {target} ...", file=sys.stderr)
        blocks = resolver(target)
        if validate(blocks, target):
            if range_start is None:
                range_start = target
        elif range_start is not None:
            range_list.append((range_start, target))
            range_start = None
            ok = False
    return ok, range_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--algo",
        choices=resolvers,
        default="gofai",
        help="Select an algorithm, default: %(default)r",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enter interactive mode",
    )
    parser.add_argument(
        "-p", "--pickle-file",
        help="Generate pickle file w/ the valid combinations"
    )
    parser.add_argument(
        "-s", "--start",
        default=min_target,
        help="range start (inclusive), default: %(default)s",
    )
    parser.add_argument(
        "-e", "--end",
        default=max_target,
        help="range end (inclusive), default: %(default)s",
    )

    args = parser.parse_args()
    resolver = resolvers[args.algo]

    start = max(args.start, min_target)
    end = min(args.end, max_target)

    if args.interactive:
        loop = True
        while loop:
            try:
                target = int(input('target> '))
                blocks = resolver(target)
                if validate(blocks, target):
                    print(f"{blocks} -> {sum(blocks)}")
            except EOFError:
                loop = False
            except (ValueError, TypeError):
                pass
    elif args.pickle_file:
        target_to_blocks = {}
        for target in range(start, end+1):
            blocks = resolver(target)
            if validate(blocks, target):
                target_to_blocks[target] = normalize_blocks(blocks)
        with open(args.pickle_file, 'wb') as f:
            pickle.dump(target_to_blocks, f)
    else:
        ok, range_list = test_range(start, end, resolver)
        longest_range = (-1, -1)
        for range in range_list:
            if range[1] - range[0] > longest_range[1] - longest_range[0]:
                longest_range = range
        print(f"[{start}, {end-1}]: ok={ok}, longest_range={longest_range}")
