#!/bin/bash

# This script takes input from curate.py and creates verifier image.
# The script is called only when attestation is required by the user.

# The input parameters in sequence are below:
#   Argument                      Expected
#   number                         Value
# -- arg1    : 'done' means user provided his own certs in verifier/ssl directory, else the default
#               non-production ready certs will be used. The certs are finally copied to ssl_common
#               directory for future use by gsc image and the verifier image.
# -- arg2    :  encryption key path. When this variable is set, then `CMD ["key-path"]` will be
#               appended to verifier.dockerfile
echo printing args $0 $@

rm -rf gramine >/dev/null 2>&1
# TODO: After release of gramine v1.3, replace master with v1.3 in below line
git clone --depth 1 https://github.com/gramineproject/gramine.git && cd gramine && git checkout master

cd CI-Examples/ra-tls-secret-prov
make clean && make ssl/server.crt >/dev/null 2>&1
cd ../../../

rm -rf  ssl_common >/dev/null 2>&1
mkdir -p ssl_common

if [ "$1" = "done" ]; then
    cd ssl
    cp ca.crt server.crt server.key ../ssl_common
    cd ..
else
    cd gramine/CI-Examples/ra-tls-secret-prov/ssl
    cp ca.crt server.crt server.key ../../../../ssl_common
    cd ../../../../
fi

cp verifier.dockerfile.template verifier.dockerfile

if [ ! -z "$2" ]; then
    echo 'CMD ["'$2'"]' >> verifier.dockerfile
fi

docker rmi -f verifier_image >/dev/null 2>&1
docker build -f verifier.dockerfile -t verifier .

rm verifier.dockerfile 2>&1
rm -rf gramine >/dev/null 2>&1
