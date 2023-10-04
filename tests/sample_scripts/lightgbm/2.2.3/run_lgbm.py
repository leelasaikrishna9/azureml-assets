# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""
This file is called LightGBM Estimator and passes parameters to Light GBM executable.

It is part of AzureML SDK.
"""

import os
from shutil import copyfile
import time
import subprocess
import argparse
import re
from azureml.core import Run
from threading import Event, Thread


def _retry(func, *args, retry_count=5, delay=5, allowed_exceptions=()):
    for i in range(retry_count):
        try:
            result = func(*args)
            if result:
                return result
        except allowed_exceptions:
            print("Waiting for {0} seconds before trying again", delay)
            time.sleep(delay)
            if i == (retry_count - 1):
                print("Maximum no of retries reached for {0}. continuing on", func)


def _parse_log_metric(line, rank):
    runcontext = _retry(Run.get_context, allowed_exceptions=Exception)
    match_result = re.search(r'Iteration:(\d+)\,\s(training|valid_1)\s(\w+)@?(\d?)\s:\s([+-]?\d+\.\d+)', line, re.I)
    if match_result:
        _retry(runcontext.log, "{0}@{1}_{2}_rank_{3}".format(match_result.group(3), match_result.group(4),
               match_result.group(2), rank), float(match_result.group(5)), allowed_exceptions=Exception)
    iteration_match = re.search(r'(\d+\.\d+)\sseconds\selapsed\,\sfinished\siteration\s(\d+)', line, re.I)
    if iteration_match:
        runcontext.log_row(name="Iteration Time", Rank=int(rank), Iteration=int(iteration_match.group(2)),
                           ElapsedSec=float(iteration_match.group(1)))
    dataload_match = re.search(r'Finished\sloading\sdata\sin\s(\d+\.\d+)\sseconds', line, re.I)
    if dataload_match:
        _retry(runcontext.log, "DataLoad Time", float(dataload_match.group(1)),
               allowed_exceptions=Exception)


def _readlog_post_metric(logfile, rank, wait_handle, error=None):
    try:
        # reading command line output in 4M buffers
        chunk_size_bytes = int(4 * 1000 * 1024)
        sleep_interval_sec = 2
        with open(logfile, "r") as data:
            while True:
                lines = data.readlines(chunk_size_bytes)
                if lines:
                    for line in lines:
                        if line.strip() != '\n':
                            print(line, end='')
                            _parse_log_metric(line, rank)
                elif wait_handle.isSet():
                    return
                wait_handle.wait(sleep_interval_sec)
    except Exception:
        raise


def _run_lgbm(rank, train_conf_file, args, trainconf_param_args, subprocess):
    prefix = ''
    lgbm_path = prefix + '/LightGBM/lightgbm'
    conf_path = train_conf_file
    cmd_fmt = '{0} config={1}'
    cmd = cmd_fmt.format(lgbm_path, conf_path)
    print('Running command {0}'.format(cmd))
    lightgbmlog = "lightgbm_log{0}.txt".format(rank)
    return_code = None
    if args.data:
        data_file = args.data[int(rank)]
        trainconf_param_args.append("data={}".format(data_file))
    if args.valid:
        validation_file = args.valid[int(rank)]
        trainconf_param_args.append("valid={}".format(validation_file))
    try:
        with open(lightgbmlog, "w") as file:
            lgbml_log_wait_handle = Event()
            read_post_metric_thread = Thread(target=_readlog_post_metric,
                                             args=(lightgbmlog, rank, lgbml_log_wait_handle))
            read_post_metric_thread.daemon = True
            read_post_metric_thread.start()
            finalcommand = []
            finalcommand.append(lgbm_path)
            finalcommand.append("config={0}".format(conf_path))
            for trainconf_param in trainconf_param_args:
                finalcommand.append(trainconf_param)
            print('Executing command {0}'.format(finalcommand))
            subprocess.check_call(finalcommand, stdout=file, stderr=file, close_fds=False)
            print('Completed running LGBM')
            return_code = 0
    except subprocess.CalledProcessError as ex:
        return_code = ex.returncode
        raise
    finally:
        print("Script process exited with code " + str(return_code))
        lgbml_log_wait_handle.set()
        read_post_metric_thread.join()


def _copy_model_file(mpi_mode):
    rank = 0
    if mpi_mode is True:
        rank = os.environ['OMPI_COMM_WORLD_RANK']

    if int(rank) == 0:
        output_dir = './outputs/model'
        os.makedirs(output_dir, exist_ok=True)
        default_model_file = 'LightGBM_model.txt'
        output_path = os.path.join(output_dir, default_model_file)
        print("copying from {0} to {1}", default_model_file, output_path)
        copyfile(default_model_file, output_path)


if __name__ == "__main__":
    mpi_mode = 'OMPI_COMM_WORLD_RANK' in os.environ

    parser = argparse.ArgumentParser("LightGBM_executor")
    parser.add_argument("--train_conf_file", type=str, default=None, help="path of config file")
    parser.add_argument("--task", type=str, default=None,
                        help="choose the type of task: train, predict, convert_model, and refit")
    parser.add_argument("--objective", type=str, default=None, help="objective of training")
    parser.add_argument("--boosting", type=str, default=None,
                        help="choose the type of boosting method to use: gbdt, rf, dart, goss")
    parser.add_argument("--data", nargs='+', default=None, help="file location for training data")
    parser.add_argument("--valid", nargs='+', default=None, help="file location for test/validation data")
    parser.add_argument("--num_iterations", type=int, default=None, help="number of iterations")
    parser.add_argument("--learning_rate", type=float, default=None, help="learning rate")
    parser.add_argument("--num_leaves", type=int, default=None, help="number of leaves")
    parser.add_argument("--tree_learner", type=str, default=None, help="type of tree learner")
    parser.add_argument("--num_threads", type=int, default=None, help="number of threads for LightGBM")
    parser.add_argument("--seed", type=int, default=None, help="this seed is used to generate other seeds")

    args, extra_args = parser.parse_known_args()
    print('args is {0}'.format(args.__dict__))

    trainconf_param_args = []

    for key, value in vars(args).items():
        if value and key != 'train_conf_file' and key != 'data' and key != 'valid':
            trainconf_param_args.append("{}={}".format(key, value))

    print('kwargs is {0}'.format(extra_args))
    it = iter(extra_args)
    for x in it:
        if next(it, None):
            trainconf_param_args.append("{}={}".format(x, next(it)))

    train_conf_file = args.train_conf_file

    if mpi_mode:
        print("In mpi mode")
        rank = os.environ['OMPI_COMM_WORLD_RANK']
        print('World rank is {0}'.format(rank))
        size = os.environ['OMPI_COMM_WORLD_SIZE']
        print('World size is {0}'.format(size))
        _run_lgbm(rank, train_conf_file, args, trainconf_param_args, subprocess)
    else:
        print("In single node mode")
        _run_lgbm('0', train_conf_file, args, trainconf_param_args, subprocess)

    _copy_model_file(mpi_mode)
