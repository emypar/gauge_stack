import sys

from . import blockset_81

def normalize_blocks(blocks):
    if blocks is not None:
        return tuple(sorted(blocks, reverse=True))


def cmp_blocks(blocks1, blocks2):
    ''' Return -1, 0, 1 if blocks1 is worse, equal or better that blocks2

    Criteria:
        - shorter block lists are better
        - for equal length block lists, then one with more larger blocks is
          better
    '''
    if blocks1 is None:
        return -1 if blocks2 is not None else 0
    if blocks2 is None:
        return 1 if blocks1 is not None else 0
    l1, l2 = len(blocks1), len(blocks2)
    if l1 < l2:
        return 1
    if l1 > l2:
        return -1
    blocks1, blocks2 = normalize_blocks(blocks1), normalize_blocks(blocks2)
    return (
        -1 if blocks1 < blocks2 else
        0 if blocks1 == blocks2 else
        1
    )
    


def sanity_check(blocks):
    used_blocks = set()
    ok = True
    for b in blocks:
        if b in used_blocks:
            print(f"{b}: used more than once", file=sys.stderr)
            ok = False
        else:
            used_blocks.add(b)
    invalid_blocks =  used_blocks - blockset_81
    if invalid_blocks:
        print(f"{invalid_blocks}: invalid blocks", file=sys.stderr)
        ok = False
    return ok

def validate(blocks, target):
    if blocks is None:
        print(f"Cannot resolve valid target {target}", file=sys.stderr)
        return False
    if not sanity_check(blocks):
        print(f"{target}: failed sanity check\n", file=sys.stderr)
        return False
    got_target = sum(blocks)
    if target != got_target:
        print(f"want: {target}, got: {blocks} -> {got_target}, diff: {target - got_target}", file=sys.stderr)
        return False
    return True
