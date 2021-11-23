#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2021 Intel Corporation
#                    Yunge Zhu <yunge.zhu@intel.linux.com>

set -e

if  [ ! -n "$1" ] ; then
    tag=latest
else
    tag=$1
fi

# You can remove build-arg http_proxy and https_proxy if your network doesn't need it
proxy_server="http://child-prc.intel.com:913" # your http proxy server

DOCKER_BUILDKIT=0 docker build \
    -f gramine_tf_serving.dockerfile . \
    -t gramine_tf_serving:${tag} \
    --build-arg http_proxy=${proxy_server} \
    --build-arg https_proxy=${proxy_server} \
    --build-arg no_proxy=localhost,127.0.0.0/1
