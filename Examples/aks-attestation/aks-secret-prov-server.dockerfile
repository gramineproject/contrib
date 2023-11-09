FROM ubuntu:20.04

RUN echo "deb http://security.ubuntu.com/ubuntu focal-security main" | tee /etc/apt/sources.list.d/focal-security.list

RUN env DEBIAN_FRONTEND=noninteractive apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    curl \
    lsb-release \
    libssl1.1 \
    pkg-config

#COPY keys/* /usr/share/keyrings/

# Installing Azure DCAP Quote Provider Library (az-dcap-client).
# Here, the version of az-dcap-client should be in sync with the az-dcap-client
# version used for quote generation. User can replace the below package with the
# latest package.

# enable Microsoft software repository
RUN curl -fsSLo /usr/share/keyrings/microsoft.asc https://packages.microsoft.com/keys/microsoft.asc
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | \
 tee /etc/apt/sources.list.d/msprod.list

RUN curl -fsSLo /usr/share/keyrings/intel-sgx-deb.asc https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sgx-deb.asc] https://download.01.org/intel-sgx/sgx_repo/ubuntu $(lsb_release -sc) main" \
|  tee /etc/apt/sources.list.d/intel-sgx.list

RUN curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ $(lsb_release -sc) main" \
| tee /etc/apt/sources.list.d/gramine.list

RUN env DEBIAN_FRONTEND=noninteractive apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    az-dcap-client \
    gramine

WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/ssl ./ssl

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov /usr/local/bin

ENTRYPOINT ["./server_dcap"]