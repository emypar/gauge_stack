#! /usr/bin/env python3

from itertools import combinations

import logging
import os
import pickle
import signal
import sys
import time

from . import blockset_81

this_dir = os.path.dirname(os.path.abspath(__file__))
gauge_dir = os.path.dirname(this_dir)
default_work_dir = os.environ.get('GAUGE_WORK_DIR', os.path.join(gauge_dir, '.work'))
default_combo_pkl_file = os.path.join(gauge_dir, "combo.pkl")

# The cutoff size for parallelism, i.e. shorter blocks are generated in the main process:
parallel_cutoff = 6

log = logging.getLogger("combo")
logHandler = logging.StreamHandler()
logHandler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
log.addHandler(logHandler)
log.setLevel(logging.INFO)


def n_choose_k(n, k):
    numerator, denominator = 1, 1
    for i in range(1, k+1):
        numerator *= (n - i + 1)
        denominator *= i
    return numerator // denominator

def _generate_combo_batch(r, prefix=None, suffix_set=blockset_81, check_combo=None):
    ''' Generate combinations of length r for targets not in check_combo

    Input:
        r (int): the desired length of the block list 
        
        prefix (iterable): all combinations should start by prefix, use None 
            for no prefix
        
        suffix_set (iterable): all combinations should end with a suffix from
             suffix_set without the blocks from prefix
        
        check_combo (set or dict): an object containing all the targets resolved
            to a block shorter than r.

    Return:
        dict[int]tuple: the best combinations for a given target, unless the
            target already exists in check_combo. If multiple combinations yield
            the same target, the one with more large blocks is preferred.        
    '''

    if prefix is None:
        prefix = tuple()
    elif prefix is not tuple:
        prefix = tuple(prefix)
    
    if len(prefix) > r:
        return None
    elif len(prefix) == r:
        target = sum(prefix)
        if check_combo is None or target not in check_combo:
            return {target: prefix}
        else:
            return None
    
    if suffix_set is not set:
        suffix_set = set(suffix_set)   
    suffix_set = suffix_set - set(prefix)
    if len(suffix_set) == 0:
        return None
    combos = {}
    prefix_target = sum(prefix)
    for suffix in combinations(suffix_set, r - len(prefix)):
        target = prefix_target + sum(suffix)
        if check_combo is not None and target in check_combo:
            continue
        # Convert combo into a tuple of blocks in decreasing order. The higher
        # tuple is preferred, since it has more large blocks. 
        combo = tuple(sorted(prefix + suffix, reverse=True))
        if target not in combos or combo > combos[target]:
            combos[target] = combo
    return combos

def generate_combo_batch(r, prefix=None, suffix_set=blockset_81, check_combo=None, pkl_file=None):
    ''' Like _generate_combo_batch, but additionally may save the result into a pickle file.
    '''
    combos = _generate_combo_batch(r, prefix=prefix, suffix_set=suffix_set, check_combo=check_combo)
    if pkl_file is not None:
        t_pkl_file = pkl_file + "_"
        with open(t_pkl_file, 'wb') as f:
            pickle.dump(combos, f)
        os.rename(t_pkl_file, pkl_file)
    else:
        return combos

def generate_combos(r, n_parallel=None, check_combo=None, _work_dir=default_work_dir):
    ''' Generate combinations of length r for targets not in check_combo with parallelism
    '''

    if n_parallel is None or n_parallel <= 0:
        n_parallel=max(os.cpu_count()//2, 1)
    if r <= parallel_cutoff or len(blockset_81) - r <= parallel_cutoff or n_parallel == 1:
        log.info(f"Generating combos for r={r} w/o parallelism")
        return generate_combo_batch(r, check_combo=check_combo) or {}
    
    for prefix_sz in range(1, max(r//2, 1) + 1):
        if n_choose_k(len(blockset_81), prefix_sz) >= n_parallel:
            break
    log.info(f"Generating combos for r={r} w/ prefix_sz={prefix_sz}, n_parallel={n_parallel}")
    
    os.makedirs(_work_dir, exist_ok=True)
    my_pid = os.getpid()

    combos = {}

    pending_pids = {}

    def wait_pids_report_err(threshold=0):
        try:
            while len(pending_pids) > threshold:
                pid, exit_code = os.wait()
                if pid in pending_pids:
                    description = pending_pids[pid]['description']
                    d_time = time.time() - pending_pids[pid]['start']
                    pkl_file = pending_pids[pid]['pkl_file']
                    stdout_file = pending_pids[pid]['out_file']
                    stderr_file = pending_pids[pid]['err_file']
                    del pending_pids[pid]
                    if exit_code == 0:
                        with open(pkl_file, 'rb') as f:
                            work_combos = pickle.load(f)
                        keep_count, total_count = 0, 0
                        if work_combos is not None:
                            total_count = len(work_combos)
                            for target, combo in work_combos.items():
                                if target not in combos or combo > combos[target]:
                                    combos[target] = combo
                                    keep_count += 1
                        log.info(
                            f"pid: {pid}, {description} completed in {d_time:.06f} sec, keep {keep_count} out of {total_count} new combos"
                        )
                        for file_path in [pkl_file, stdout_file, stderr_file]:
                            os.unlink(file_path)
                    else:
                        log.warn(
                            f"pid: {pid}, {description} completed in {d_time:.06f} sec w/ exit_code: {exit_code}, results not processed. See:"
                            + "\n\t"
                            + "\n\t".join([stdout_file, stderr_file])
                            + "\nfor details."
                        )
                        return True
                else:
                    log.warn(f"Unexpected pid={pid}, exit_code={exit_code}")
        except Exception as e:
            log.warn(f"Unexpected exception: {e}")
            return True
        return False

    # Make provisions for killing all workers:
    def kill_workers():
        log.warn("Killing all pending workers")
        for pid in pending_pids:
            log.warn(f"Killing pid={pid}")
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception as e:
                log.warn(f"Unexpected exception: {e}")
        while len(pending_pids) > 0:
            pid, exit_code = os.wait()
            log.warn(f"pid: {pid}, exit_code: {exit_code}")
            del pending_pids[pid]

    saved_sighandlers = {}

    def sighandler(sig, stackframe):
        log.warn(f"Received signal {sig} ({signal.Signals(sig).name})")
        kill_workers()
        sys.exit(sig << 8)

    for sig in [
        signal.SIGINT, 
        signal.SIGTERM, 
        signal.SIGABRT, 
        signal.SIGBUS,
    ]:
        saved_sighandlers[sig] = signal.signal(sig, sighandler)

    def restore_sighandlers():
        for sig in list(saved_sighandlers):
            signal.signal(sig, saved_sighandlers[sig])
            del saved_sighandlers[sig]

    prefix_total, iter_num = n_choose_k(len(blockset_81), prefix_sz), 0
    for prefix in combinations(blockset_81, prefix_sz):
        iter_num += 1
        prefix = tuple(sorted(prefix))
        # To avoid duplicated work, only suffixes made of blocks > max(prefix)
        # should be considered:
        suffix_set = set(b for b in blockset_81 if b > prefix[-1])
        if len(prefix) + len(suffix_set) < r:
            continue
        # Ensure that at most n_parallel jobs are running at a time; wait as needed:
        if wait_pids_report_err(threshold=n_parallel-1):
            # Worker error, abandon du travail:
            kill_workers()
            combos = None
            break
        work_file_root = os.path.join(_work_dir, '-'.join(map(str, prefix)) + f"-{len(suffix_set)}-{my_pid}-{time.time():.06f}")
        pkl_file = work_file_root + ".pkl"
        stdout_file = work_file_root + ".out"
        stderr_file = work_file_root + ".err"
        candidate_num = n_choose_k(len(suffix_set), r - len(prefix))
        description = f"r: {r}, prefix_sz: {prefix_sz}, step: {iter_num}/{prefix_total}, candidate#: {candidate_num}"
        pid = os.fork()
        if pid != 0:
            pending_pids[pid] = {
                'description': description,
                'start': time.time(),
                'pkl_file': pkl_file,
                'out_file': stdout_file,
                'err_file': stderr_file,
            }
            log.info(f"pid: {pid}, {description}, started")
        else:
            os.setsid()
            stdin_fh = open("/dev/null")
            stdout_fh = open(stdout_file, "wt")
            stderr_fh = open(stderr_file, "wt")
            os.dup2(stdin_fh.fileno(), sys.stdin.fileno())       
            os.dup2(stdout_fh.fileno(), sys.stdout.fileno())
            os.dup2(stderr_fh.fileno(), sys.stderr.fileno())
            generate_combo_batch(r, prefix=prefix, suffix_set=suffix_set, check_combo=check_combo, pkl_file=pkl_file)
            sys.exit(0)
    if wait_pids_report_err():
        combos = None
    restore_sighandlers()
    return combos


def update_combo_pkl_file(
        max_len=parallel_cutoff, 
        n_parallel=None, 
        combo_pkl_file=default_combo_pkl_file,
        _work_dir=default_work_dir,
):
    '''Update combo file with all combos of size <= max_len
    '''
    log.info(f"Check/update {combo_pkl_file} for max_len={max_len}")
    combo_pkl_dir = os.path.dirname(combo_pkl_file)
    os.makedirs(combo_pkl_dir, exist_ok=True)

    # Acquire lock:
    combo_pkl_file_lck = f"{combo_pkl_file}.lck"
    try:
        lock_f = open(combo_pkl_file_lck, 'a+')
        os.lockf(lock_f.fileno(), os.F_TLOCK, 0)
    except Exception as e:
        log.warn(f"Cannot acquire lock {combo_pkl_file_lck}: {e}")
        return

    # Load the previous file, if any, and determine its max size:
    log.info("Load previous file, if any")
    try:
        all_combos, prev_max_len = {}, 0
        with open(combo_pkl_file, 'rb') as f:
            all_combos = pickle.load(f)
    except FileNotFoundError as e:
        log.warn(e)
    if all_combos:
        prev_max_len = max(map(len, all_combos.values()))
    log.info(f"Previous max_len={prev_max_len}, num_targets={len(all_combos)}")
    if prev_max_len >= max_len:
        log.info(f"File up to date, nothing to be done")
    else:
        new_combo_count = 0
        start_all = time.time()
        for r in range(prev_max_len+1, max_len+1):
            start = time.time()
            combos = generate_combos(r, n_parallel=n_parallel, check_combo=all_combos, _work_dir=_work_dir)
            d_time = time.time() - start
            if combos is None:
                log.warn("Error, file will not be updated")
                return None
            else:
                common_targets = set(combos).intersection(all_combos)
                if len(common_targets) > 0:
                    log.fatal(f"r={r}, common_targets={common_targets}")
                    return None
                new_combo_count += len(combos)
                log.info(f"{len(combos)} combos of size {r} generated in {d_time:.06f} sec")
                if len(combos) > 0:
                    all_combos.update(combos)
                    with open(combo_pkl_file, 'wb') as f:
                        pickle.dump(all_combos, f)
                    log.info(f"{combo_pkl_file} updated, max_len={r}, num_targets={len(all_combos)}")  
        d_time = time.time() - start_all
        log.info(f"{new_combo_count} total combos generated in {d_time:.06f} sec")
    os.lockf(lock_f.fileno(), os.F_ULOCK, 0)
    return all_combos



