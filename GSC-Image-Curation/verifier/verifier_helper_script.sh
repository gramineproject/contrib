#!/bin/bash

rm -rf gramine >/dev/null 2>&1
git clone --depth 1 https://github.com/gramineproject/gramine.git

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

cp verifier.dockerfile.template verifier.dockerfile

if [ ! -z "$2" ]; then
    echo 'CMD ["'$2'"]' >> verifier.dockerfile
fi

docker rmi -f verifier_image >/dev/null 2>&1
docker build -f verifier.dockerfile -t verifier .

rm verifier.dockerfile 2>&1
rm -rf gramine >/dev/null 2>&1