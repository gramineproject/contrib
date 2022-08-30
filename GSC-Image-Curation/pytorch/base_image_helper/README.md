This directory contains steps and artifacts to create a docker image with plaintext/encrypted files.

We will use PyTorch example available here https://github.com/gramineproject/examples/blob/master/pytorch/
to demonstrate the base image creation with plaintext/encrypted files.

- Execute `bash ./helper.sh` command to create base image with plaintext files or 
- Execute `bash ./helper.sh encrypt` command to encrypt the files and create base image with
encrypted files.

File Encryption is done using `gramine-sgx-pf-crypt` tool and encryption key `wrap-key` provided here.
`gramine-sgx-pf-crypt` tool is part of gramine installation, please install gramine, if not done
 already by following the instructions available here
 https://gramine.readthedocs.io/en/latest/quickstart.html#install-gramine

Please refer `GSC-Image-Curation/README.md` to curate the image created in above steps with GSC.
