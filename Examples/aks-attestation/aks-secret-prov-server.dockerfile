FROM ubuntu:18.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gnupg2 \
    wget \
    curl

# Installing Azure DCAP Quote Provider Library (az-dcap-client).
# Here, the version of az-dcap-client should be in sync with the az-dcap-client
# version used for quote generation. User can replace the below package with the
# latest package.
RUN wget https://packages.microsoft.com/ubuntu/18.04/prod/pool/main/a/az-dcap-client/az-dcap-client_1.10_amd64.deb \
 && dpkg -i az-dcap-client_1.10_amd64.deb

WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/ssl ./ssl
COPY gramine/CI-Examples/ra-tls-secret-prov/files ./files

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov_server_dcap /usr/local/bin

RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

# Install Gramine dcap package.
RUN curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | tee /etc/apt/sources.list.d/gramine.list
RUN apt-get update
RUN apt-get install -y gramine-dcap

ENTRYPOINT ["secret_prov_server_dcap"]
