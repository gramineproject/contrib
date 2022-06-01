sudo curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | sudo tee /etc/apt/sources.list.d/gramine.list

curl -fsSL https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add -
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list

sudo apt-get update
sudo apt-get install gramine-dcap # for out-of-tree DCAP driver (required by AKS Ubuntu 18.04 distro)

gramine-sgx-gen-private-key

git clone https://github.com/gramineproject/gramine.git --depth=1
cd gramine && git fetch --all --tags && git checkout v1.2

# Copy dummy server certificate with Common Name as "<AKS-DNS-NAME.*.cloudapp.azure.com>
cd ../
cp -r ssl/* gramine/CI-Examples/ra-tls-secret-prov/ssl
