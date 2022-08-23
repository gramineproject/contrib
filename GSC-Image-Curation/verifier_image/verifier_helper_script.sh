#!/bin/bash
rm -rf gramine >/dev/null 2>&1

/bin/sh install_gramine.sh

cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make dcap >/dev/null 2>&1
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

docker rmi -f verifier_image >/dev/null 2>&1
docker build -f verifier.dockerfile -t verifier_image .

rm -rf gramine >/dev/null 2>&1
