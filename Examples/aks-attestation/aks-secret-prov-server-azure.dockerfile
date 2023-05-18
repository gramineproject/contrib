FROM ubuntu:18.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    gnupg2 \
    wget

# enable Microsoft software repository
curl -fsSLo /usr/share/keyrings/microsoft.asc https://packages.microsoft.com/keys/microsoft.asc
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.asc] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | \
    tee /etc/apt/sources.list.d/msprod.list

# install Azure DCAP library
apt update
apt install -y az-dcap-client

# restart the AESM service; Gramine Docker image provides a helpful script
/restart_aesm.sh


WORKDIR /ra-tls-secret-prov

COPY gramine/CI-Examples/ra-tls-secret-prov/ssl ./ssl
COPY gramine/CI-Examples/ra-tls-secret-prov/files ./files

COPY gramine/CI-Examples/ra-tls-secret-prov/secret_prov_server_dcap /usr/local/bin

RUN echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' \
    > /etc/apt/sources.list.d/intel-sgx.list \
    && wget https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    && apt-key add intel-sgx-deb.key

RUN curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
RUN echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | tee /etc/apt/sources.list.d/gramine.list
RUN apt-get update
RUN apt-get install -y gramine-dcap

ENTRYPOINT ["secret_prov_server_dcap"]