#! /usr/bin/env python3

''' Compare pickle files
'''

import argparse
from collections import defaultdict
import pickle
import os
from tabulate import tabulate

from algo.validator import cmp_blocks

def load_pkl_file(pkl_file):
    with open(pkl_file, 'rb') as f:
        return pickle.load(f)


def generate_total_count(target_to_blocks_by_file, tablefmt="pretty"):
    pkl_files = sorted(target_to_blocks_by_file)
    headers = [
        os.path.basename(pkl_file) for pkl_file in pkl_files
    ]
    table = [
        [len(target_to_blocks_by_file[pkl_file]) for pkl_file in pkl_files]
    ]
    colalign = ["right"] * len(headers)
    return tabulate(table, headers=headers, colalign=colalign, tablefmt=tablefmt)


def generate_count_by_len(target_to_blocks_by_file, tablefmt="pretty"):
    '''' Generate the report with
    len(blocks): number_of_targets, number_of_targets, ..., number_of_targets
    '''
    pkl_files = sorted(target_to_blocks_by_file)
    headers = ["Length"] + [
        os.path.basename(pkl_file) for pkl_file in pkl_files
    ]
    count_by_len_file = {}
    for i, pkl_file in enumerate(pkl_files):
        count_by_len = defaultdict(int)
        for blocks in target_to_blocks_by_file[pkl_file].values():
            count_by_len[len(blocks)] += 1
        for l, n in  count_by_len.items():
            if l not in count_by_len_file:
                count_by_len_file[l] = [None] * len(pkl_files)
            count_by_len_file[l][i] = n
    table = [
        [l] + count_by_len_file[l] for l in sorted(count_by_len_file)
    ]
    colalign = ["right"] * len(headers)
    return tabulate(table, headers=headers, colalign=colalign, tablefmt=tablefmt)

def generate_cumulative_count_by_len(target_to_blocks_by_file, tablefmt="pretty"):
    '''' Generate the report with
    len(blocks) <= L: number_of_targets (%), number_of_targets (%), ..., number_of_targets
    '''
    pkl_files = sorted(target_to_blocks_by_file)
    headers = ["Length <="] + [
        os.path.basename(pkl_file) for pkl_file in pkl_files
    ]
    count_by_len_file = {}
    total_count_by_file = {}
    for i, pkl_file in enumerate(pkl_files):
        count_by_len = defaultdict(int)
        total_count_by_file[pkl_file] = len(target_to_blocks_by_file[pkl_file])
        for blocks in target_to_blocks_by_file[pkl_file].values():
            count_by_len[len(blocks)] += 1
        for l, n in  count_by_len.items():
            if l not in count_by_len_file:
                count_by_len_file[l] = [0] * len(pkl_files)
            count_by_len_file[l][i] = n

    cumulative_count_by_len_file = {}
    cumulative_pct_by_len_file = {}
    prev_count = [0] * len(pkl_files)
    for l in sorted(count_by_len_file):
        cumulative_count_by_len_file[l] = list(count_by_len_file[l])
        for i in range(len(pkl_files)):
            cumulative_count_by_len_file[l][i] += prev_count[i]
            prev_count[i] = cumulative_count_by_len_file[l][i]
    cumulative_pct_by_len_file = {}
    for l, cumulative_count_by_file in cumulative_count_by_len_file.items():
        cumulative_pct_by_file = {}
        for file_name, count in cumulative_count_by_file.items():
            cumulative_pct_by_file[file_name] = count / 
    table = [
        [l] + cumulative_count_by_len_file[l] for l in sorted(cumulative_count_by_len_file)
    ]
    colalign = ["right"] * len(headers)
    return tabulate(table, headers=headers, colalign=colalign, tablefmt=tablefmt)


def cmp_pkl_files(target_to_blocks_by_file, pkl_file1, pkl_file2, tablefmt="pretty"):
    ''' Generate the report with
    len(blocks): file1 better#, same#, worse# 
    '''
    t2b1, t2b2 = target_to_blocks_by_file[pkl_file1], target_to_blocks_by_file[pkl_file2]
    cmp_count_by_len = {}
    for target in t2b1:
        if target not in t2b2:
            continue
        blocks1, blocks2 = t2b1[target], t2b2[target]
        l = len(blocks1)
        if l not in cmp_count_by_len:
            cmp_count_by_len[l] = [0, 0, 0]
        cmp_1v2 = cmp_blocks(blocks1, blocks2)
        if cmp_1v2 == -1:
            cmp_count_by_len[l][2] += 1
        elif cmp_1v2 == 0:
            cmp_count_by_len[l][1] += 1
        else:
            cmp_count_by_len[l][0] += 1
    headers = ["Length", "Better#", "Same#", "Worse#"]
    table = [
        [l] + cmp_count_by_len[l] for l in sorted(cmp_count_by_len)
    ]
    colalign = ["right"] * len(headers)
    return tabulate(table, headers=headers, colalign=colalign, tablefmt=tablefmt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("pkl_file", nargs="+")
    args = parser.parse_args()
    pkl_files = args.pkl_file
    target_to_blocks_by_file = {
        pkl_file: load_pkl_file(pkl_file) for pkl_file in pkl_files
    }
    print(
        "Target Count Total:\n",
        generate_total_count(target_to_blocks_by_file),
        "\n\n",
        sep='',
    )

    print(
        "Target Count By Length Of Block Resolution:\n",
        generate_count_by_len(target_to_blocks_by_file),
        "\n\n",
        sep='',
    )

    print(
        "Target Count By Cumulative Length Of Block Resolution:\n",
        generate_cumulative_count_by_len(target_to_blocks_by_file),
        "\n\n",
        sep='',
    )

    for i in range(len(pkl_files)):
        for j in range(len(pkl_files)):
            if i == j:
                continue
            print(
                f"Compare {pkl_files[i]} v. {pkl_files[j]}:\n",
                cmp_pkl_files(target_to_blocks_by_file, pkl_files[i], pkl_files[j]),
                "\n\n",
                sep='',
            )
