#!/bin/bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# This script takes input from curate.py and creates verifier image.
# The script is called only when attestation is required by the user.

# The input parameters in sequence are below:
# -- arg1    : 'done' means user provided his own certs in verifier/ssl directory, else the default
#               non-production ready certs will be used. The certs are finally copied to ssl_common
#               directory for future use by gsc image and the verifier image.
# -- arg2    :  encryption key path. When this variable is set, then `CMD ["key-path"]` will be
#               appended to verifier.dockerfile
echo printing args $0 $@

rm -rf  ssl_common >/dev/null 2>&1
mkdir -p ssl_common

if [ "$1" = "done" ]; then
    cd ssl
    cp ca.crt server.crt server.key ../ssl_common
    cd ..
else
    rm -rf gramine >/dev/null 2>&1
    # TODO: After release of gramine v1.3, replace commit SHA with v1.3 in below line
    git clone https://github.com/gramineproject/gramine.git && cd gramine &&
    git checkout 4f259b80ed4c40e7cccde70e822d378754dacb97

    cd CI-Examples/ra-tls-secret-prov
    make clean && make ssl/server.crt >/dev/null 2>&1
    cd ssl
    cp ca.crt server.crt server.key ../../../../ssl_common
    cd ../../../../
    rm -rf gramine >/dev/null 2>&1
fi

cp verifier.dockerfile.template verifier.dockerfile

args=''
# Use `secret_prov_pf` if base image have encrypted files
if [ "$2" = "y" ]; then
    sed -i 's|secret_prov_minimal|secret_prov_pf|g' verifier.dockerfile
    args="--build-arg server_dcap_pf=y"
fi

if [ ! -z "$3" ]; then
    echo 'CMD ["'$3'"]' >> verifier.dockerfile
fi

docker rmi -f verifier_image >/dev/null 2>&1
docker build -f verifier.dockerfile -t verifier $args .
