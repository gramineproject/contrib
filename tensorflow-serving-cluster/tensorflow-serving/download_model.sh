#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2021 Intel Corporation
#                    Yunge Zhu <yunge.zhu@intel.linux.com>

set -e

cur_dir=`pwd -P`
models_abs_dir=${cur_dir}/models
mkdir ${models_abs_dir}

# resnet50-v15
mkdir ${models_abs_dir}/resnet50-v15-fp32
cd ${models_abs_dir}/resnet50-v15-fp32
wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_8/resnet50_fp32_pretrained_model.pb -O resnet50-v15-fp32.pb
