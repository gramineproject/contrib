This directory contains steps and artifacts to create a docker image with encrypted files.

# Prerequisites

- Please install [prerequisites](https://github.com/gramineproject/examples/tree/master/pytorch#pre-requisites)
  on your machine.
- File Encryption is done using `gramine-sgx-pf-crypt` tool which is part of
  [gramine installation](https://gramine.readthedocs.io/en/latest/quickstart.html#install-gramine).
- Encryption key. We have added an encryption key in `wrap-key` file for test purpose.

# Base docker image creation

We will use PyTorch example available [here](https://github.com/gramineproject/examples/blob/master/pytorch/)
to demonstrate the base image creation with encrypted files.

- Execute `bash ./helper.sh` command to encrypt the files and create base image with
  encrypted files.

Please refer `Curated-Apps/README.md` to curate the image created in above steps with GSC.
