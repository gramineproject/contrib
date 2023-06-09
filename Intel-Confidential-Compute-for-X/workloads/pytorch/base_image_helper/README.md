This directory contains steps and artifacts to create a PyTorch Docker image containing an encrypted
model and an encrypted sample picture.

# Prerequisites
- Install dependencies:
    - Ubuntu 18.04:
        ```sh
        sudo apt install libnss-mdns libnss-myhostname python3-pip lsb-release
        python3 -m pip install --upgrade pip # on ubuntu 18.04 machine
        python3 -m pip install --user torchvision pillow
        ```
- [Install Gramine](https://gramine.readthedocs.io/en/stable/quickstart.html#install-gramine)
    as the encryption is done using the `gramine-sgx-pf-crypt` tool which is part of Gramine
    installation.
    You can learn more about Gramine's support of encrypted files in the
    [corresponding documentation](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files).


# Create base Docker image

Execute the helper script contained in this directory: `./helper.sh`.

This script clones Gramine's [PyTorch example](https://github.com/gramineproject/examples/blob/master/pytorch/);
downloads a pre-trained model; generates a weak encryption key (that must not be used in
production); encrypts an example picture and the model; and builds a Docker image containing PyTorch
the encrypted picture.

Please refer to the [README of Intel® Confidential Compute for PyTorch](../README.md)
to generate a Gramine-protected version of this Docker image.
