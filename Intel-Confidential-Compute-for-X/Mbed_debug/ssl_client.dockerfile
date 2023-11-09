# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

FROM ubuntu:22.04

RUN echo "deb http://security.ubuntu.com/ubuntu focal-security main" | tee /etc/apt/sources.list.d/focal-security.list

RUN env DEBIAN_FRONTEND=noninteractive apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    git \
    libssl1.1 \
    wget \
    pkg-config \
    python3-jsonschema


# Installing Azure DCAP Quote Provider Library (az-dcap-client).
# Here, the version of az-dcap-client should be in sync with the az-dcap-client
# version used for quote generation. User can replace the below package with the
# latest package.
RUN wget https://packages.microsoft.com/keys/microsoft.asc -O /usr/share/keyrings/microsoft.asc
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" \
    | tee /etc/apt/sources.list.d/msprod.list 

RUN wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key -O /usr/share/keyrings/intel-sgx-deb.key
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sgx-deb.key] https://download.01.org/intel-sgx/sgx_repo/ubuntu focal main' > /etc/apt/sources.list.d/intel-sgx.list

RUN wget https://packages.gramineproject.io/gramine-keyring.gpg -O /usr/share/keyrings/gramine-keyring.gpg
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ 1.4 main' \
    | tee /etc/apt/sources.list.d/gramine.list

RUN env DEBIAN_FRONTEND=noninteractive apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    az-dcap-client \
    gramine

RUN git clone --depth 1 --branch v1.4 https://github.com/gramineproject/gramine.git

ARG server_dcap_pf="n"
RUN if [ $server_dcap_pf="y" ]; then \
        sed -i "s|verify_measurements_callback,|NULL,|g" \
        "gramine/CI-Examples/ra-tls-secret-prov/secret_prov_pf/server.c"; \
    fi

RUN mkdir -p /ra-tls-secret-prov/secret_prov_minimal
RUN cd gramine/CI-Examples/ra-tls-secret-prov/ \
    && make clean && make dcap \
    && cp secret_prov_minimal/server_dcap /ra-tls-secret-prov/secret_prov_minimal/

RUN rm -rf gramine >/dev/null 2>&1

# first copy certs from /verifier/ssl 
COPY ssl/* /ra-tls-secret-prov/ssl/ 

RUN git clone https://github.com/Mbed-TLS/mbedtls.git

WORKDIR /mbedtls/programs

RUN make

WORKDIR ssl

ENTRYPOINT ["./ssl_client2"]

CMD ["server_addr="]
