#! /usr/bin/env python3

''' Convert pickle file to .h for C lookup
'''

import argparse
import pickle
import sys
import zlib

from algo import blockset_81

details = '''
/* 

Data for target resolution lookup 
=================================

The blocks are described by a LABELS array:

    LABELS[0], LABELS[1], ..., LABELS[N-1]

Each pre-resolved target has a solution represented by a N-bit bitmap:

    b(n-1)b(n-2)...b0

where b(k) is set if block(k) is part of the solution.

The bitmaps for all resolvable targets in ascending order are concatenated
together, at bit level, in a BITMAPS byte array.

The resolvable targets fall within a MIN_TARGET .. MAX_TARGET interval (the ends
are included). But not all targets are resolvable, there are ranges and gaps
between them.

The target to bitmap resolution is described by an array of structures, one
entry for each resolvable range:

    RANGE[i]:
        RANGE_START, RANGE_END 
        BIT_OFFSET_BASE

The array above is sorted in ascending order:

    RANGE[i-1].RANGE_END < RANGE[i].RANGE_START, for all 1 <= i

The BIT_OFFSET_BASE is the global bit offset in BITMAPS where b0 (LS bit, that
is) for RANGE_START is.

For a target T, RANGE_START <= T <= RANGE_END, the bit offset for b0 in BITMAPS
is:

    BIT_OFFSET_BASE + (T - RANGE_START)*BITMAP_NUM_BITS

therefore the bit offset for b_k, (0 <= k <= BITMAP_NUM_BITS-1), is:

    off_k = BIT_OFFSET_BASE + (T - RANGE_START)*BITMAP_NUM_BITS + k

Since BITMAPS is stored as bytes, the following formula represents the test for
block(k) (and LABELS[k]):


    BITMAPS[off_k >> 3] & (1 << (off_k & 7))


The pseudo code for resolving target T:

    Locate RANGE[i] such that RANGE_START <= T <= RANGE_END. 
    
    If none found, then the target is not resolvable.

    Otherwise:

    bit_offset_start <- RANGE[i].BIT_OFFSET_BASE + (T - RANGE[i].RANGE_START)*BITMAP_NUM_BITS


    For raw bitmaps:
        solution <- empty
        for k in 0 .. (N-1) do
            off_k <- bit_offset_start + k
            if BITMAPS[off_k >> 3] & (1 << (off_k & 7)) then
                add LABELS[k] to the solution

    For compressed bitmaps:
        Create de-compression stream from bitmaps
        byte_offset_start <- bit_offset_start >> 3
        Read byte_offset_start from the compression stream
        bitmap <- read ((BITMAP_NUM_BITS + 7) >> 3) bytes from the compression stream
        bitmap_offset <- bit_offset_start & 7
        for k in 0 .. (N-1) do
            off_k <- bitmap_offset_start + k
            if bitmap[off_k >> 3] & (1 << (off_k & 7)) then
                add LABELS[k] to the solution

*/
'''

STORAGE_MACRO = "PROGMEM"

LABELS_VAR_NAME = "labels"
BITMAPS_VAR_NAME = "bitmaps"
RANGE_STRUCT_NAME = "range"
RANGES_VAR_NAME = "ranges"


MiB = 0x100000

def print_preamble(fh=None, storage=STORAGE_MACRO):
    if fh is None:
        fh = sys.stdout
    print(
        details,
        end='', sep='', file=fh,       
    )
    print(
f'''
#ifndef {storage}
# define {storage}
#endif
''',
        end='', sep='', file=fh,       
    )


def print_labels(labels, fh=None, var_name=LABELS_VAR_NAME, storage=STORAGE_MACRO):
    if fh is None:
        fh = sys.stdout
    print(
f'''
const char* {var_name}[] {storage} = {{ \\
''',
        end='', sep='', file=fh,
    )
    indent = ' ' * 4
    first_line = True
    for label in labels:
        if not first_line:
            print(
                f", \\\n",
                end='', sep='', file=fh,
            )
        else:
            first_line = False
        print(
            indent,
            f'"{label}"',
            end='', sep='', file=fh,
        )


    print(
'''
};

''',
        end='', sep='', file=fh,
    )


def print_bitmaps(
    buf, fh=None, var_name=BITMAPS_VAR_NAME, storage=STORAGE_MACRO, 
    entries_per_line=16,
    is_compressed=False,
):
    if fh is None:
        fh = sys.stdout
    if is_compressed:
        var_name += "_z"
        print(
'''
/*
   Note: bitmap is compressed!
 */
''',
            end='', sep='', file=fh,
        )
    print(
f'''
const uint8_t {var_name}[] {storage} = {{ \\
''',
        end='', sep='', file=fh,
    )

    indent = ' ' * 4
    first_line = True
    for i in range(0, len(buf), entries_per_line):
        if not first_line:
            print(
                f", \\\n",
                end='', sep='', file=fh,
            )
        else:
            first_line = False
        print(
            indent,
            ", ".join(f"0x{b:02x}" for b in buf[i:i+entries_per_line]),
            end='', sep='', file=fh,
        )

    print(
'''
};

''',
        end='', sep='', file=fh,
    )

def print_ranges(ranges, fh=None, var_name=RANGES_VAR_NAME, storage=STORAGE_MACRO):
    if fh is None:
        fh = sys.stdout

    bitmap_num_bits = len(blockset_81) 
    print(
f'''
#define MIN_TARGET (uint32_t){ranges[0][0]}
#define MAX_TARGET (uint32_t){ranges[-1][0]}
#define BITMAP_NUM_BITS {bitmap_num_bits}

struct {RANGE_STRUCT_NAME} {{
    uint32_t start, end;
    uint32_t bit_off_base;
}};

const struct {RANGE_STRUCT_NAME} {var_name}[] {storage} = {{ \\
''',
        end='', sep='', file=fh,
    )

    bit_off_base = 0
    indent = ' ' * 4
    first_line = True
    for start, end in ranges:
        if not first_line:
            print(
                f", \\\n",
                end='', sep='', file=fh,
            )
        else:
            first_line = False
        print(
            indent,
            f"{{{start}, {end}, {bit_off_base}}}",
            end='', sep='', file=fh,
        )
        bit_off_base += (end - start + 1) * bitmap_num_bits

    print(
f'''
}};

#define NUM_RANGES {len(ranges)}

''',
        end='', sep='', file=fh,
    )



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--out-file",
        default="bitmap.h",
        help="Bitmap header file, default: %(default)s",
    )
    parser.add_argument(
        "-z", "--zlib-compress",
        action='store_true',
        help="Compress the bitmaps array",
    )

    parser.add_argument("pkl_file")
    args = parser.parse_args()

    out_file = args.out_file
    if out_file == "-":
        out_file = None

    # Ensure that the blockset is sorted, build the value -> index map, and the
    # label list:
    blockset_81 = sorted(blockset_81)
    labels = [f"{b/10000:.04f}" for b in blockset_81]
    label_index_map = {b: i for i, b in enumerate(blockset_81)}


    # Load pickle file and check its min target:
    with open(args.pkl_file, 'rb') as f:
        target_to_blocks = pickle.load(f)
    targets = sorted(target_to_blocks)
    if len(targets) == 0:
        print("Empty pickle file", file=sys.stderr)
        exit(1)

    # Determine target ranges:
    min_target, max_target = targets[0], targets[-1]
    target_ranges = []
    range_start, range_end = min_target, min_target
    for target in targets[1:]:
        if target != range_end + 1:
            target_ranges.append((range_start, range_end))
            range_start = target
        range_end = target
    target_ranges.append((range_start, range_end))

    # Build the bitmaps:
    bitmap_num_bits = len(blockset_81)
    bitmap_num_bits_total = 0
    for range_start, range_end in target_ranges:
        bitmap_num_bits_total += (range_end - range_start + 1) * bitmap_num_bits
    buf = bytearray((bitmap_num_bits_total + 7) >> 3)
    range_bit_off_base = 0
    for range_start, range_end in target_ranges:
        for target in range(range_start, range_end + 1):
            bit_off_base = range_bit_off_base + (target - range_start) * bitmap_num_bits
            for block in target_to_blocks[target]:
                bit_off = bit_off_base + label_index_map[block]
                buf[bit_off >> 3] |= (1 << (bit_off & 7))
        range_bit_off_base += (range_end - range_start + 1) * bitmap_num_bits
    
    if args.zlib_compress:
        raw_sz = len(buf)
        buf = zlib.compress(buf, level=zlib.Z_BEST_COMPRESSION)
        print(
            f"bitmaps: {raw_sz/MiB:.03f} -> {len(buf)/MiB:.03f} MiB after compression",
            file=sys.stderr,
        )

    # Generate the file:
    fh = open(out_file, "wt") if out_file is not None else None
    print_preamble(fh=fh)
    print_labels(labels, fh=fh)
    bitmaps_var_name = BITMAPS_VAR_NAME
    print_bitmaps(buf, fh=fh, is_compressed=args.zlib_compress)
    print_ranges(target_ranges, fh=fh)

    # Estimate storage requirement:
    bitmap_storage_bytes = len(buf)
    ranges_storage_bytes = len(target_ranges) * 3 * 4
    storage_bytes = bitmap_storage_bytes + ranges_storage_bytes
    brute_force_storage_bytes = (max_target - min_target + 1) * ((bitmap_num_bits + 7) >> 3)
    saved_storage_bytes = brute_force_storage_bytes - storage_bytes
    print(
        f"Storage: {bitmap_storage_bytes/MiB:.03f} (bitmaps) + " +
        f"{ranges_storage_bytes/MiB:.03f} (ranges) = " +
        f"{storage_bytes/MiB:.03f} MiB\n" +
        f"Brute force storage: {brute_force_storage_bytes/MiB:.03f} MiB\n" + 
        f"Saved: {saved_storage_bytes/MiB:.03f} MiB",
        file=sys.stderr
    )


    if out_file is not None:
        fh.close()
        print(f"{out_file} generated", file=sys.stderr)

    