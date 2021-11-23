#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2021 Intel Corporation
#                    Yunge Zhu <yunge.zhu@intel.linux.com>

set -e

function usage_help() {
    echo -e "options:"
    echo -e "  -h Display help"
    echo -e "  -i {image_id}"
    echo -e "  -p {host_ports}"
    echo -e "  -m {model_name}"
    echo -e "  -s {ssl_config_file}"
}

# Default args
host_ports=""
cur_dir=`pwd -P`
ssl_config_file=""
enable_model_warmup=true
flush_filesystem_caches=false
enable_batching=false
rest_api_num_threads=64
session_parallelism=0
parallel_num_threads=32
file_system_poll_wait_seconds=5
http_proxy=""
https_proxy=""
no_proxy=""

# Override args
while getopts "h?r:i:p:m:s:" OPT; do
    case $OPT in
        h|\?)
            usage_help
            exit 1
            ;;
        i)
            echo -e "Option $OPTIND, image_id = $OPTARG"
            image_id=$OPTARG
            ;;
        p)
            echo -e "Option $OPTIND, host_ports = $OPTARG"
            host_ports=$OPTARG
            ;;
        m)
            echo -e "Option $OPTIND, model_name = $OPTARG"
            model_name=$OPTARG
            ;;
        s)
            echo -e "Option $OPTIND, ssl_config_file = $OPTARG"
            ssl_config_file=$OPTARG
            ;;
        :)
            echo -e "Option $OPTARG needs argument"
            usage_help
            exit 1
            ;;
        ?)
            echo -e "Unknown option $OPTARG"
            usage_help
            exit 1
            ;;
    esac
done

docker run -d --rm -p ${host_ports}:8500-8501 \
    -e MODEL_NAME=${model_name} \
    -e OMP_NUM_THREADS=${parallel_num_threads} \
    -e MKL_NUM_THREADS=${parallel_num_threads} \
    -v ${cur_dir}/models:/models \
    -v ${cur_dir}/ssl_configure/${ssl_config_file}:/${ssl_config_file} \
    ${image_id} \
        --enable_batching=${enable_batching} \
        --enable_model_warmup=${enable_model_warmup} \
        --flush_filesystem_caches=${flush_filesystem_caches} \
        --rest_api_num_threads=${rest_api_num_threads} \
        --tensorflow_session_parallelism=${session_parallelism} \
        --tensorflow_intra_op_parallelism=${parallel_num_threads} \
        --tensorflow_inter_op_parallelism=${parallel_num_threads} \
        --file_system_poll_wait_seconds=${file_system_poll_wait_seconds}\
        --ssl_config_file=/${ssl_config_file}
