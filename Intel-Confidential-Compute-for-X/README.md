# Intel® Confidential Compute for X

The "Intel® Confidential Compute for X" project provides an interactive script to transform regular
Docker images to Gramine-protected (aka, graminized) Docker images. The transformation adds
important features, e.g., attestation, to the original Docker image to enable secure end-to-end use
cases. The interactive script asks users for necessary configurations, and provides these inputs to
[GSC](https://github.com/gramineproject/gsc) for the actual transformation.

One main goal of the project is to prepare the necessary script settings and templates so that a
graminized Docker image for well-known applications can be created in minutes. At the moment,
Intel® carefully prepared the script for the following applications:

* [Intel® Confidential Compute for Redis](workloads/redis/)
* [Intel® Confidential Compute for PyTorch](workloads/pytorch/)
* [Intel® Confidential Compute for TensorFlow Serving](workloads/tensorflow-serving/)
* [Intel® Confidential Compute for Scikit-learn](workloads/sklearn/)
* [Intel® Confidential Compute for Memcached](workloads/memcached/)
* [Intel® Confidential Compute for MySQL](workloads/mysql/)
* [Intel® Confidential Compute for MariaDB](workloads/mariadb/)
* [Intel® Confidential Compute for OpenVINO Model Server](workloads/openvino-model-server/)

For these applications, the interactive script also provides a test feature. With a single command,
users can generate a non-production, Gramine-protected Docker image. This image is signed with a
dummy key and must only be used for experimentation and learning.

One can easily graminize more applications with the interactive script by studying the prepared
application, and adjusting the settings and templates as needed.


## Prerequisites

### For building an "Intel® Confidential Compute for X" image

- No hardware requirements.
- Any regular system with a Linux distribution is sufficient.
- Install the necessary build dependencies and adjust the permissions of `/var/run/docker.sock` for
  the current user:
   - Ubuntu 20.04
        ```sh
        sudo apt-get update && sudo apt-get install -y docker.io python3 python3-pip
        python3 -m pip install docker jinja2 tomli tomli-w pyyaml
        sudo chown $USER /var/run/docker.sock
        ```

### For executing an "Intel® Confidential Compute for X" image

#### Hardware requirements

- SGX-enabled Azure VMs:

  At Azure, VMs of the [DCsv3 and DCdsv3-series](https://learn.microsoft.com/en-us/azure/virtual-machines/dcv3-series)
  should be used. Azure provides a
  [quickstart guide](https://learn.microsoft.com/en-us/azure/confidential-computing/quick-create-portal)
  to setup such VMs. During the selection of the VM, one has to carefully select a machine
  providing the necessary amount of EPC memory suiting the application. A table with the
  provided EPC memory size can be found on the
  [DCsv3 and DCdsv3-series overview](https://learn.microsoft.com/en-us/azure/virtual-machines/dcv3-series).

- Bare-metal systems:

  User is expected to have DCAP remote attestation infrastructure with PCCS setup and system
  provisioned. Please follow instructions [here](https://www.intel.com/content/www/us/en/developer/articles/guide/intel-software-guard-extensions-data-center-attestation-primitives-quick-install-guide.html)
  for DCAP remote attestation setup.

#### Install the necessary build dependencies:

Below commands are specific to Ubuntu 20.04. Please follow the instructions under
`"Intel® SGX Application User"` section in document [here](https://download.01.org/intel-sgx/latest/dcap-latest/linux/docs/Intel_SGX_SW_Installation_Guide_for_Linux.pdf)
for other distro specific commands.

```sh
sudo apt-get update && sudo apt-get install -y docker.io
sudo chown $USER /var/run/docker.sock

echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu focal main' |
    sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO - https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key |
    sudo apt-key add -
sudo apt-get install -y -f libsgx-dcap-ql libsgx-dcap-default-qpl=1.16.100.2-focal1

# Execute below command (only on Azure VM) to change PCCS_URL to Azure PCCS
sudo sed -i "s|^\(  \"pccs_url\": \"https://\).*\(/sgx/certification.*\)|\1global.acccache.azure.net\2|g" \
    /etc/sgx_default_qcnl.conf
```

## Usage of the interactive script

```sh
python3 curate.py <app name> <base image name> <optional args>
```

For detailed usage information:

```sh
python3 curate.py --help
```
## Contents

    .
    |-- curate.py  # Interactive script that does the transformation explained above.
    |-- util/      # Helper scripts and files that curate.py uses.
    |-- verifier/  # Contents to build attestation verifier image.
    |-- workloads/ # Contains  script settings and templates for prepared applications.
