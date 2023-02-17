# Gramine Curated Applications

The Gramine Curated applications project provides an interactive script that helps to transform any
Docker image to a graminized one, packing features such as attestation and beyond, necessary for
enabling end-to-end use cases securely. The interactive script asks users for specific
requirements, and submits the user inputs to the [GSC tool](https://github.com/gramineproject/gsc).
A list of workload examples are provided below for reference. One can easily extend these reference
examples to support more workloads by inspecting the contents of any of the reference workloads
(e.g. `workloads/redis/` directory), understand how they work, and then use them as the basis for
 their own workloads. The script also provides a `test` feature where, with a single command, users
can generate a non-production GSC image, signed with a dummy key, purely for experimentation and
learning.

## Prerequisites

### For building curated GSC image
- No hardware requirements.
- Any regular system with a Linux distribution is sufficient.
- Install the necessary build dependencies as shown below (for Ubuntu).
  ```sh
  sudo apt-get update && sudo apt-get install jq docker.io python3 python3-pip
  python3 -m pip install docker jinja2 toml pyyaml
  sudo chown $USER /var/run/docker.sock
  ```

### For running the curated GSC image
1. [Create an Intel SGX VM from the Azure portal](https://learn.microsoft.com/en-us/azure/confidential-computing/quick-create-portal).
   The tested distros are Ubuntu and Debian. Selection of a VM must factor in the EPC size that
   suits the application.

2. Install the necessary build dependencies as shown below (for Ubuntu 18.04).
   ```sh
   sudo apt-get update && sudo apt-get install -y docker.io
   sudo chown $USER /var/run/docker.sock
   echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu bionic main' |
       sudo tee /etc/apt/sources.list.d/intel-sgx.list
   wget -qO - https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key |
       sudo apt-key add -
   sudo apt-key adv --fetch-keys https://packages.microsoft.com/keys/microsoft.asc
   sudo apt-add-repository 'https://packages.microsoft.com/ubuntu/18.04/prod main'
   sudo apt update && sudo apt install -y az-dcap-client
   sudo apt-get install -y -f libsgx-dcap-ql
   ```

## Interactive script usage
```sh
python3 curate.py <workload type> <base image name> <optional args>
```

    |---------------------------------------------------------------------------------------------|
    | S.No.| Required?| Argument         | Description/Possible values                            |
    |------|----------|------------------|--------------------------------------------------------|
    | 1.   |    Yes   | <workload type>  | Type of workload (refer to workload/ sub-directory     |
    |      |          |                  | for full list of supported workload types) e.g. redis. |
    | 2.   |    Yes   | <base image name>| Base image name to be graminized.                      |
    | 3.   | Optional | 'debug'          | To generate an insecure graminized image with debug    |
    |      |          |                  | symbols.                                               |
    | 4.   | Optional | 'test'           | To generate an insecure image with a test enclave      |
    |      |          |                  | signing key.                                           |
    |---------------------------------------------------------------------------------------------|

## Sample Workloads
`workloads/` subdirectory contains relevant instructions and support files to curate a selected
 set of applications with Gramine.

## Contents

    .
    |-- curate.py               # Entry file for curation that the user runs as explained above
    |-- util/                   # Helper scripts and files that curate.py uses
    |-- verifier/               # Contents to build attestation verifier image
    |-- workloads/              # Sample curated applications for select set of workloads
