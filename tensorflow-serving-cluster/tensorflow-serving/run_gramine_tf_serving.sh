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
    echo -e "  -a {attestation_hosts}"
    echo -e "       Format: '{attestation_domain_name}:{ip}'"
    echo -e "  -e {sgx_env}"
    echo -e "       SGX = sgx_env"
}

# Default args
SGX=1
host_ports=""
cur_dir=`pwd -P`
ssl_config_file=""
enable_batching=false
rest_api_num_threads=64
session_parallelism=0
parallel_num_threads=32
file_system_poll_wait_seconds=5
attestation_hosts="localhost:127.0.0.1"
work_base_path=/gramine/Examples/tensorflow-serving-cluster/tensorflow-serving
isgx_driver_path=/gramine/driver/driver/linux/include
http_proxy=""
https_proxy=""
no_proxy=""

# Override args
while getopts "h?r:i:p:m:s:a:e:" OPT; do
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
        a)
            echo -e "Option $OPTIND, attestation_hosts = $OPTARG"
            attestation_hosts=$OPTARG
            ;;
        e)
            echo -e "Option $OPTIND, SGX = $OPTARG"
            SGX=$OPTARG
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


docker run \
    -it \
    --device /dev/sgx \
    --add-host=${attestation_hosts} \
    -p ${host_ports}:8500-8501 \
    -v ${cur_dir}/models:${work_base_path}/models \
    -v ${cur_dir}/ssl_configure/${ssl_config_file}:${work_base_path}/${ssl_config_file} \
    -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
    -e http_proxy=${http_proxy} \
    -e https_proxy=${https_proxy} \
    -e no_proxy=${no_proxy} \
    -e SGX=${SGX} \
    -e ISGX_DRIVER_PATH=${isgx_driver_path} \
    -e WORK_BASE_PATH=${work_base_path} \
    -e model_name=${model_name} \
    -e ssl_config_file=/${ssl_config_file} \
    -e enable_batching=${enable_batching} \
    -e rest_api_num_threads=${rest_api_num_threads} \
    -e session_parallelism=${session_parallelism} \
    -e intra_op_parallelism=${parallel_num_threads} \
    -e inter_op_parallelism=${parallel_num_threads} \
    -e OMP_NUM_THREADS=${parallel_num_threads} \
    -e MKL_NUM_THREADS=${parallel_num_threads} \
    -e file_system_poll_wait_seconds=${file_system_poll_wait_seconds} \
    ${image_id}
