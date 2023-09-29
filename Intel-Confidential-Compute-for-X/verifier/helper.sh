#!/bin/bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# This script takes input from curate.py and creates verifier image.
# The script is called only when attestation is required by the user.

# The input parameters in sequence are below:
# -- arg1    : 'done' means user provided his own certs in verifier/ssl directory or
#              'test' means non-production ready certs will be used.
#              The certs are finally copied to ssl_common directory for future use by GSC image and
#              the verifier image.
# -- arg2    : y or n (encrypted files to be used with workload?)
# -- arg3    : Encryption key path. `CMD ["key-path"]` instruction will be appended to
#              verifier.dockerfile when this variable is set.

set -e
echo printing args $0 $@

MY_PATH=$(dirname "$0")
pushd ${MY_PATH}

docker rmi -f verifier >/dev/null 2>&1
rm -rf  ssl_common >/dev/null 2>&1
mkdir -p ssl_common

if [ "$1" = "done" ]; then
    cp -f ssl/ca.crt ssl/server.crt ssl/server.key ssl_common/
else
    openssl genrsa -out ssl_common/ca.key 2048
    openssl req -x509 -new -nodes -key ssl_common/ca.key -sha256 -days 1024 -out ssl_common/ca.crt -config ca_config.conf
    openssl genrsa -out ssl_common/server.key 2048
    openssl req -new -key ssl_common/server.key -out ssl_common/server.csr -config ca_config.conf
    openssl x509 -req -days 360 -in ssl_common/server.csr -CA ssl_common/ca.crt -CAkey ssl_common/ca.key -CAcreateserial -out ssl_common/server.crt
fi

cp -f verifier.dockerfile.template verifier.dockerfile

args=''
# Use `secret_prov_pf` if base image has encrypted files
if [ "$2" = "y" ]; then
    args="--build-arg server_dcap_type=secret_prov_pf"
fi

# Add encryption key path
if [ ! -z "$3" ]; then
    echo 'CMD ["'$3'"]' >> verifier.dockerfile
fi

cd ..
docker build -f verifier/verifier.dockerfile -t verifier $args .
