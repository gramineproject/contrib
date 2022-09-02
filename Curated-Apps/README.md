# Gramine Curated Applications

The Gramine Curated applications project provides an interactive script that helps to transform any
Docker image to a graminized one, packing features such as attestation and beyond, necessary for
enabling end-to-end use cases securely. The interactive script asks users for specific
requirements, and submits the user inputs to the [GSC tool](https://github.com/gramineproject/gsc).
A list of workload examples are provided below for reference. One can easily extend these reference
examples to supporting more workloads by inspecting the contents of any of the reference workloads
(for e.g. `redis/` directory), understand how they work, and then use them as the basis for their
own workloads. The script also provides a `test` feature where, with a single command, users
can generate a non-production GSC image, signed with a dummy key, purely for experimentation and
learning.

## Prerequisites

```sh
$ sudo apt-get install jq
$ sudo apt-get install docker.io python3 python3-pip
$ pip3 install docker jinja2 toml pyyaml
```
Install [Gramine](https://gramine.readthedocs.io/en/latest/quickstart.html#install-gramine) for
encrypted files support.

## Interactive script usage:
`python3 curate.py <workload type> <base image name> <optional args>`
    |----------------------------------------------------------------------------------------------------|
    | Required?| Argument           | Description/Possible values                                        |
    |----------|--------------------|--------------------------------------------------------------------|
    |    Yes   | `<Workload type>`  | Provide type of workload e.g., redis or pytorch etc..              |
    |    Yes   | `<base image name>`| Base image name to be graminized.                                  |
    | Optional | 'debug'            | To generate graminized image with debug symbols for debugging.     |
    | Optional | 'test'             | To generate no-production image with a test enclave signing key.   |
    |----------------------------------------------------------------------------------------------------|

## Sample Workloads

### Redis

To generate a non-production test graminized image

`$ python3 ./curate.py redis redis:7.0.0 test`

To generate a custom graminized image, follow the below. This will launch an interactive application
that will take inputs to create a curated graminized image.

`$ python3 ./curate.py redis <your image>`

### Pytorch

User is expected to first have his base image `<base_image_with_pytorch>` ready with PyTorch and
the necessary application files built into this image. `/pytorch` directory contains sample
dockerfiles and instructions to create a test pytorch base image. This base image is then passed to
the curation application `curate.py` as shown below.

To generate a non-production test graminized image

`$ python3 ./curate.py pytorch <base_image_with_pytorch> test`

To generate a custom graminized image, follow the below.
This will launch an interactive script that will take inputs to create a curated graminized
image.

`$ python3 ./curate.py pytorch <base_image_with_pytorch>`


## Contents

    .
    ├── curate.py               # Entry file for curation that the user runs as explained above
    ├── redis/                  # Contents to help curate.py with GSC Redis curation
    ├── pytorch/                # Contents to help curate.py with GSC PyTorch curation
    ├── util/                   # Helper scripts and files that curate.py uses
    ├── verifier/               # Contents to build attestaton verifier image
