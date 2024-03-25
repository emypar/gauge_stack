#! /usr/bin/env python3

from . import blockset_81 

# The greedy match may not succeed on the original target. Retry an adjusted
# target, by trying to pre-allocate one of the smaller blocks:
adjustment_blocks = [0] + [
    b for b in sorted(blockset_81) if b < 1500 and b % 10 == 0
]
min_block = min(blockset_81)


# Greedy match digit N:
def get_digit_n(val, n):
    digit = val
    for _ in range(n):
        digit = digit // 10
    return digit % 10

def greedy_match_digit_n(target, n, available_blocks, blocks):
    digit = get_digit_n(target, n)
    if digit == 0:
        return target
    lookup_blocks = sorted(available_blocks)
    min_b = lookup_blocks[0]
    lookup_blocks = reversed(lookup_blocks)
    for b in lookup_blocks:
        if b > target:
            continue
        b_digit = get_digit_n(b, n)
        if b_digit == digit and target - b >= min_b:
            blocks.append(b)
            available_blocks.discard(b)
            return target - b
    return target
  
def greedy_match(target, available_blocks, blocks):
    candidates = sorted(available_blocks, reverse=True)
    crt, n = 0, len(candidates)
    while target > 0 and crt < n:
        b = candidates[crt]
        if b <= target:
            blocks.append(b)
            target -= b
            available_blocks.discard(b)
        crt += 1
    return target


def resolve(target):
    # Edge case, direct match.
    if target in blockset_81:
        return [target]
    best_target_deficit = None
    best_blocks = None
    for adj_b in adjustment_blocks:
        target_deficit = target - adj_b
        if target_deficit < min_block:
            break
        blocks = []
        available_blocks = set(blockset_81)
        if adj_b > 0:
            blocks.append(adj_b)
            available_blocks.discard(adj_b)
        target_deficit = greedy_match_digit_n(target_deficit, 0, available_blocks, blocks)
        target_deficit = greedy_match_digit_n(target_deficit, 1, available_blocks, blocks)
        target_deficit = greedy_match(target_deficit, available_blocks, blocks)
        if (
                best_target_deficit is None 
                or target_deficit < best_target_deficit 
                or target_deficit == best_target_deficit and len(blocks) < len(best_blocks)
        ):
            best_blocks = blocks
            best_target_deficit = target_deficit
        if best_target_deficit == 0:
            break
    return best_blocks
