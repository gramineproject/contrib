sudo curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | sudo tee /etc/apt/sources.list.d/gramine.list

curl -fsSL https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add -
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu $(lsb_release -cs) main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt-get update
sudo apt-get install gramine-dcap # for out-of-tree DCAP driver (required by AKS Ubuntu 18.04 distro)

sudo apt-get install libsgx-dcap-quote-verify-dev

######### dependences
sudo apt-get install -y build-essential \
    autoconf bison gawk nasm ninja-build pkg-config python3 python3-click \
    python3-jinja2 python3-pip python3-pyelftools wget
sudo python3 -m pip install 'meson>=0.56' 'tomli>=1.1.0' 'tomli-w>=0.4.0'

##require pip3 install protobuf==3.20.3

gramine-sgx-gen-private-key

git clone --depth 1 https://github.com/gramineproject/gramine.git --branch v1.4

# Copy dummy server certificate with Common Name as "<AKS-DNS-NAME.*.cloudapp.azure.com>
cp -r ssl/* gramine/CI-Examples/ra-tls-secret-prov/ssl

