#! /usr/bin/env python3

from collections import deque

from . import blockset_81, min_target, max_target


# The problem at hand is converting a uv.wxyz into a stack of blocks, ideally
# the minimum number of blocks, such that sum(blok values) matched the uv.wxyz
# number (u, v, w, x, y, z are digits).
#
# Initially we are looking for the max contiguous range uv.wxyz-UV.WXYZ such
# each value in the range can  be expressed. 
#
# Unless a number matches a block exactly, we need at least 2 blocks, hence min
# >= .1000 + .0500 = .1500 . Evidently some values such as .1999 can be
# accommodated so we'll assume that min .2000 . For max value, the integer part
# uv can take any value in the 1-10 range using the 1.0000, 2.0000, 3.0000,
# 4.0000 blocks. We'll assume that max value is 11.1999 .
#
# We'll use the following logic for .2000-11.9999 values, loosely inspired by
# dynamic programming (memoization of smaller results).
#
## +---------+-----------------------------------------------+-----------------------------+
## | Target  | Conditions                                    | Blocks                      |
## +---------+-----------------------------------------------+-----------------------------+
## | 0.2000  | v = 0, w = 2, x = 0, y = 0, z = 0             | .2000                       |
## | 0.2xyz  | v = 0, w = 2, x = 0-4, y = 0-9, z = 0-9       | .100z, .1xy0                |
## | 0.2500  | v = 0, w = 2, x = 5, y = 0, z = 0             | .2500                       |
## | 0.250z  | v = 0, w = 2, x = 5, y = 0, z = 0-9           | .1500, .100z                |
## | 0.2xy0  | v = 0, w = 2, x = 5-9, y = 0-9, z = 0         | .1500, .1(x-5)y0            |
## | 0.2xyz  | v = 0, w = 2, x = 5-9, y = 0-9, z = 0-9       | .0500, .100z, .1(x-5)y0     |
## +---------+-----------------------------------------------+-----------------------------+
## | 0.w000  | v = 0, w = 3 - 9, x = 0, y = 0, z = 0         | .w000                       |
## | 0.w00z  | v = 0, w = 3 - 9, x = 0, y = 0, z = 1-9       | .(w-1)000, .100z            |
## | 0.wxy0  | v = 0, w = 3 - 9, x = 0-4, y = 0-9, z = 0     | .(w-1)000, .1xy0            |
## | 0.wxyz  | v = 0, w = 3 - 9, x = 0-4, y = 0-9, z = 1-9   | .(w-2)000, .100z, .1xy0     |
## | 0.w500  | v = 0, w = 3 - 9, x = 5, y = 0, z = 0         | .w500                       |
## | 0.wxyz  | v = 0, w = 3 - 9, x = 5-9, y = 0-9, z = 0-9   | .(w-2)500, .100z, .1(x-5)y0 |
## +---------+-----------------------------------------------+-----------------------------+
## | 1.000z  | v = 1, w = 0, x = 0, y = 0, z = 0-9           | .9000, .100z                |
## | 1.0xy0  | v = 1, w = 0, x = 0-4, y = 0-9, z = 0         | .9000, .1xy0                |
## | 1.0xyz  | v = 1, w = 0, x = 0-4, y = 0-9, z = 1-9       | .8000, .100z, .1xy0         |
## | 1.0500  | v = 1, w = 0, x = 5, y = 0, z = 0             | .8500, .2000                |
## | 1.0xyz  | v = 1, w = 0, x = 5-9, y = 0-9, z = 0-9       | .8500, .100z, .1(x-5)y0     |
## +---------+-----------------------------------------------+-----------------------------+
## | 1.1000  | v = 1, w = 1, x = 0, y = 0, z = 0             | .9000, .2000                |
## | 1.100z  | v = 1, w = 1, x = 0, y = 0, z = 1-9           | .9000, .1000, .100z         |
## | 1.1xyz  | v = 1, w = 1, x = 0-4, y = 0-9, z = 0-9       | .9000, .100z, .1xy0         |
## | 1.1500  | v = 1, w = 1, x = 5, y = 0, z = 0             | .9500, .2000                |
## | 1.1xyz  | v = 1, w = 1, x = 5-9, y = 0-9, z = 0-9       | .9500, .100z, .1(x-5)y0     |
## +---------+-----------------------------------------------+-----------------------------+
## The above covers the .2000-1.1999 range using blocks < 1.0000; the integer
# blocks extend the range to 11.1999.
#
# The only block that could have been used twice is .1000 and that could happen
# for cases x = y = z = 0, or x = 5, y = z = 0. Such edge cases are prevented by
# either direct match or by explicit prior match.
#
# To further extend the range, we'll use pairs that sum up to 1.0000, e.g. .2000
# and .8000 or .2500 and .7500; there are 9 such pairs (cannot use .5000 twice).
# A solution above either contains a .x000 or a .x500 but not both. That
# eliminates one more pair so the range could be further extended by 8.
gofai_min_target = 2000

fractional_blockset_81 = set(b for b in blockset_81 if b < 10000)

# The break down for integer part uv:
integer_value_block_list = {
    0: [],
    1: [10000],
    2: [20000],
    3: [30000],
    4: [40000],
    5: [10000, 40000],
    6: [20000, 40000],
    7: [30000, 40000],
    8: [10000, 30000, 40000],
    9: [20000, 30000, 40000],
    10: [10000, 20000, 30000, 40000],
}


def reduce_fractional_blocks(blocks):
    todo = deque()
    todo.append(blocks)
    reduced_blocks = blocks
    while todo:
        try_blocks = todo.popleft()
        if len(try_blocks) < len(reduced_blocks):
            reduced_blocks = try_blocks
        if len(try_blocks) > 1:
            n = len(try_blocks)
            for i in range(n-1):
                for j in range(i+1, n):
                    merged_block = try_blocks[i] + try_blocks[j]
                    if merged_block in fractional_blockset_81:
                        todo.append(try_blocks[:i] + try_blocks[i+1:j] + [merged_block] + try_blocks[j+1:])
    return reduced_blocks

def resolve_fractional_target(vwxyz):
    # Use direct match for 0wxyz, this allows us to comment the direct match rules:
    if  vwxyz < 10000 and vwxyz in blockset_81:
        return [vwxyz]

    v = vwxyz // 10000
    w = (vwxyz // 1000) % 10
    x = (vwxyz // 100) % 10
    y = (vwxyz // 10) % 10
    z = vwxyz % 10

    ## +---------+-----------------------------------------------+-----------------------------+
    ## | 0.2000  | v = 0, w = 2, x = 0, y = 0, z = 0             | .2000                       |
    ## | 0.2xyz  | v = 0, w = 2, x = 0-4, y = 0-9, z = 0-9       | .100z, .1xy0                |
    ## | 0.2500  | v = 0, w = 2, x = 5, y = 0, z = 0             | .2500                       |
    ## | 0.2xyz  | v = 0, w = 2, x = 5-9, y = 0-9, z = 1-9       | .0500, .100z, .1(x-5)y0     |
    ## +---------+-----------------------------------------------+-----------------------------+
    # if v == 0 and w == 2 and x == 0 and y == 0 and z == 0:
    #     return [2000]
    if v == 0 and w == 2 and x < 5:
        return [1000 + z, 1000 + 100*x + 10*y]
    # if v == 0 and w == 2 and x == 5 and y == 0 and z == 0:
    #     return [2500]
    if v == 0 and w == 2 and 5 <= x:
        return [500, 1000 + z, 1000 + 100*(x-5) + 10*y]

    ## +---------+-----------------------------------------------+-----------------------------+
    ## | 0.w000  | v = 0, w = 3 - 9, x = 0, y = 0, z = 0         | .w000                       |
    ## | 0.w00z  | v = 0, w = 3 - 9, x = 0, y = 0, z = 1-9       | .(w-1)000, .100z            |
    ## | 0.wxy0  | v = 0, w = 3 - 9, x = 0-4, y = 0-9, z = 0     | .(w-1)000, .1xy0            |
    ## | 0.wxyz  | v = 0, w = 3 - 9, x = 0-4, y = 0-9, z = 1-9   | .(w-2)000, .100z, .1xy0     |
    ## | 0.w500  | v = 0, w = 3 - 9, x = 5, y = 0, z = 0         | .w500                       |
    ## | 0.wxyz  | v = 0, w = 3 - 9, x = 5-9, y = 0-9, z = 0-9   | .(w-2)500, .100z, .1(x-5)y0 |
    ## +---------+-----------------------------------------------+-----------------------------+
    # if v == 0 and 3 <= w and x == 0 and y == 0 and z == 0:
    #     return [w * 1000]
    if v == 0 and 3 <= w and x == 0 and y == 0:
        return [(w-1)*1000, 1000 + z]
    if v == 0 and 3 <= w and x < 5 and z == 0:
        return [(w-1)*1000, 1000 + 100*x + 10*y]
    if v == 0 and 3 <= w and x < 5 and 1 <= z:
        return [(w-2)*1000, 1000 + z, 1000 + 100*x + 10*y]
    # if v == 0 and 3 <= w and x == 5 and y == 0 and z == 0:
    #     return [w * 1000 + 500]
    if v == 0 and 3 <= w and 5 <= x:
        return [(w-2)*1000 + 500, 1000 + z, 1000 + 100*(x-5) + 10*y]

    ## +---------+-----------------------------------------------+-----------------------------+
    ## | 1.000z  | v = 1, w = 0, x = 0, y = 0, z = 0-9           | .9000, .100z                |
    ## | 1.0xy0  | v = 1, w = 0, x = 0-4, y = 0-9, z = 0         | .9000, .1xy0                |
    ## | 1.0xyz  | v = 1, w = 0, x = 0-4, y = 0-9, z = 1-9       | .8000, .100z, .1xy0         |
    ## | 1.0500  | v = 1, w = 0, x = 5, y = 0, z = 0             | .8500, .2000                |
    ## | 1.0xyz  | v = 1, w = 0, x = 5-9, y = 0-9, z = 0-9       | .8500, .100z, .1(x-5)y0     |
    ## +---------+-----------------------------------------------+-----------------------------+
    if v == 1 and w == 0 and x == 0 and y == 0:
        return [9000, 1000 + z]
    if v == 1 and w == 0 and x < 5 and z == 0:
        return [9000, 1000 + 100*x + 10*y]
    if v == 1 and w == 0 and x < 5 and 1 <= z:
        return [8000, 1000 + z, 1000 + 100*x + 10*y]
    if v == 1 and w == 0 and x == 5 and y == 0 and z == 0:
        return [8500, 2000]
    if v == 1 and w == 0 and 5 <= x:
        return [8500, 1000 + z, 1000 + 100*(x-5) + 10*y]

    ## +---------+-----------------------------------------------+-----------------------------+
    ## | 1.1000  | v = 1, w = 1, x = 0, y = 0, z = 0             | .9000, .2000                |
    ## | 1.100z  | v = 1, w = 1, x = 0, y = 0, z = 1 -9          | .9000, .1000, .100z         |
    ## | 1.1xyz  | v = 1, w = 1, x = 0-4, y = 0-9, z = 0-9       | .9000, .100z, .1xy0         |
    ## | 1.1500  | v = 1, w = 1, x = 5, y = 0, z = 0             | .9500, .2000                |
    ## | 1.1xyz  | v = 1, w = 1, x = 5-9, y = 0-9, z = 0-9       | .9500, .100z, .1(x-5)y0     |
    ## +---------+-----------------------------------------------+-----------------------------+
    if v == 1 and w == 1 and x == 0 and y == 0 and z == 0:
        return [9000, 2000]
    if v == 1 and w == 1 and x == 0 and y == 0 and 1 <= z:
        return [9000, 1000, 1000 + z]
    if v == 1 and w == 1 and x < 5:
        return [9000, 1000 + z, 1000 + 100*x + 10*y]
    if v == 1 and w == 1 and x == 5 and  y == 0 and z == 0:
        return [9500, 2000]
    if v == 1 and w == 1 and 5 <= x:
        return [9500, 1000 + z, 1000 + 100*(x-5) + 10*y]
    
    raise RuntimeError(f"Uncovered {vwxyz} case")       


def resolve(target):
    ''' Return the list of blocks for a target value.
        Input:
            target (int): target value 200-111999 range
        Return:
            the list subset of blockset_81 which sums up 
            to target or None if the value is outside the
            range.
    '''

    # Edge case, direct match.
    if target in blockset_81:
        return [target]
    if target < gofai_min_target or target > max_target:
        return None
    # Determine the integer quantity above 111999 that will be extended last via
    # x000, (10-x)000 or x500, (9-x)500 pairs:
    if target >= 112000:
        integer_pair_target = (target - 112000) // 10000 + 1
        adjusted_target = target - integer_pair_target * 10000
    else:
        integer_pair_target = 0
        adjusted_target = target

    # Isolate the integer blocks:
    integer_target = (adjusted_target - 2000) // 10000
    # Determine v.wxyz and fractional blocks:
    fractional_target = adjusted_target - integer_target * 10000
    fractional_blocks = sorted(resolve_fractional_target(fractional_target))
    reduced_fractional_blocks = sorted(reduce_fractional_blocks(fractional_blocks))
    # Determine integer blocks:
    integer_blocks = sorted(integer_value_block_list[integer_target])
    # If there is no integer pair target, we are done:
    if integer_pair_target == 0:
        return reduced_fractional_blocks + integer_blocks
    # Resolve the integer pair blocks:
    available_integer_pair_blocks = set(
        b for b in blockset_81 if b != 5000 and b < 10000 and b % 500 == 0
    ) - set(reduced_fractional_blocks)
    # Keep only pairs:
    for b in list(available_integer_pair_blocks):
        if 10000 - b not in available_integer_pair_blocks:
            available_integer_pair_blocks.discard(b)
    # Enough pairs?
    if len(available_integer_pair_blocks) // 2 < integer_pair_target:
        print(f"""
Not enough integer pair blocks:
    target:                         {target}
    integer_pair_target:            {integer_pair_target}
    adjusted_target:                {adjusted_target}
    fractional_blocks:              {fractional_blocks}
    reduced_fractional_blocks:      {reduced_fractional_blocks}
    available_integer_pair_blocks:  {available_integer_pair_blocks} ({len(available_integer_pair_blocks)})
        """)
        return None
    integer_pair_blocks = []
    selection_integer_pair_blocks = sorted(available_integer_pair_blocks)
    for k in range(integer_pair_target):
        b = selection_integer_pair_blocks[k]
        integer_pair_blocks.extend([b, 10000-b])
    return reduced_fractional_blocks + integer_blocks + integer_pair_blocks
    



