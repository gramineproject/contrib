sudo curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ stable main' | sudo tee /etc/apt/sources.list.d/gramine.list

curl -fsSL https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add -
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list

sudo apt-get remove gramine-dcap -y
sudo apt-get update
sudo apt-get install gramine-dcap -y # for out-of-tree DCAP driver (required by AKS Ubuntu 18.04 distro)

gramine-sgx-gen-private-key  >/dev/null 2>&1

git clone --depth 1 https://github.com/gramineproject/gramine.git
