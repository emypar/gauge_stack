#! /usr/bin/env python3

''' Convert pickle file to CSV for spreadsheet import
'''

import argparse
import os
import pickle
import sys

headers = ["Target", "Num Blocks", "Blocks"]

def format_val(val):
    return f'{val/10000:.04f}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--num-val-per-sheet",
        default=10000,
        help="Number of values per sheet, default: %(default)d",
    )
 
    parser.add_argument(
        "-o", "--out-dir",
        default="csv",
        help="Directory for CSV files, default: %(default)s",
    )
    parser.add_argument("pkl_file")
    args = parser.parse_args()

    # Load pickle file and check its min target:
    with open(args.pkl_file, 'rb') as f:
        target_to_blocks = pickle.load(f)
    targets = sorted(target_to_blocks)
    if len(targets) == 0:
        print("Empty pickle file", file=sys.stderr)
        exit(1)

    num_val_per_sheet = args.num_val_per_sheet
    out_dir = os.path.join(args.out_dir, str(num_val_per_sheet))
    os.makedirs(out_dir, exist_ok=True)

    crt_sheet_num, crt_fh, sheet_file_name = None, None, None
    for target in targets:
        sheet_num = target // num_val_per_sheet
        if sheet_num != crt_sheet_num:
            if crt_fh is not None:
                print(f"{sheet_file_name} generated", file=sys.stderr)
                crt_fh.close()
            sheet_name = (
                format_val(sheet_num * num_val_per_sheet)
                + "-"
                + format_val((sheet_num + 1)* num_val_per_sheet - 1)
            )
            sheet_file_name = os.path.join(out_dir, f"{sheet_name}.csv")
            crt_fh = open(sheet_file_name, "wt")
            print(", ".join(headers), file=crt_fh)
            crt_sheet_num = sheet_num
        blocks = sorted(target_to_blocks[target])
        line = [
            format_val(target),
            str(len(blocks)),
        ] + [format_val(b) for b in blocks]
        print(", ".join(line), file=crt_fh)
    if crt_fh is not None:
        print(f"{sheet_file_name} generated", file=sys.stderr)
        crt_fh.close()
