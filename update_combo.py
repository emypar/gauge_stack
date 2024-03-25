#! /usr/bin/env python3

import argparse
import os
import sys
import time

from algo.combo import default_work_dir, update_combo_pkl_file

parser = argparse.ArgumentParser()
parser.add_argument(
    "-b", "--bg", "--background",
    action="store_true",
    help="Run in the background"
)
parser.add_argument(
    "-n", "--n-parallel",
    default=max(os.cpu_count() - 1, 1),
    type=int,
    help="The degree of parallelism, default: %(default)d (#cores - 1)"
)
parser.add_argument(
    "n",
    type=int,
    help="Combination length"
)

args = parser.parse_args()

if args.bg:
    os.makedirs(default_work_dir, exist_ok=True)
    out_file_root = (
        os.path.basename(__file__).replace(".py", "")
        + "-"
        + time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    )
    pid_file = os.path.join(default_work_dir, out_file_root + ".pid")
    stdout_file = os.path.join(default_work_dir, out_file_root + ".out")
    stderr_file = os.path.join(default_work_dir, out_file_root + ".err")
    pid = os.fork()
    if  pid > 0:
        with open(pid_file, "wt") as f:
            print(pid, file=f)
        print(
            f"The app will run in the bg w/ pid {pid} and:\n\n"
            + f" pid -> {pid_file}\n"
            + f" out -> {stdout_file}\n"
            + f" err -> {stderr_file}\n"
        )
        exit(0)
    os.setsid()
    stdin_fh = open("/dev/null")
    stdout_fh = open(stdout_file, "wt")
    stderr_fh = open(stderr_file, "wt")
    os.dup2(stdin_fh.fileno(), sys.stdin.fileno())       
    os.dup2(stdout_fh.fileno(), sys.stdout.fileno())
    os.dup2(stderr_fh.fileno(), sys.stderr.fileno())

update_combo_pkl_file(args.n, n_parallel=args.n_parallel)

