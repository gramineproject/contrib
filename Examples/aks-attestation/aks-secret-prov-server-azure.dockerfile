FROM ubuntu:20.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    gnupg2 \
    nodejs \
    wget

# enable Microsoft software repository
RUN curl -fsSLo /usr/share/keyrings/microsoft.asc https://packages.microsoft.com/keys/microsoft.asc
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | \
    tee /etc/apt/sources.list.d/msprod.list

# install Azure DCAP library
RUN apt update
RUN apt install -y az-dcap-client

WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/ssl ./ssl
COPY gramine/CI-Examples/ra-tls-secret-prov/helper-files ./files

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov_pf /usr/local/bin

RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

RUN curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | tee /etc/apt/sources.list.d/gramine.list
RUN apt-get update
RUN apt-get install -y gramine-dcap
WORKDIR /usr/local/bin 

ENTRYPOINT ["server_dcap /usr/local/bin/wrap_key"]
