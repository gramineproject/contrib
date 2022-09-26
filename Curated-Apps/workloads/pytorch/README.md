# Gramine Curated PyTorch
In the following two sections, we explain how a Docker image for the protected PyTorch version can
be built and how the image can be executed.

## Build a confidential compute image for PyTorch
The following description assumes that the [prerequisites](https://github.com/gramineproject/contrib.git/Curated-Apps/README.md)
for building the curated image are met, and the commands below are executed on the
corresponding VM.

1. Clone the Gramine Contrib repository

       $ git clone https://github.com/gramineproject/contrib.git

2. Move to the Curated-Apps folder

       $ cd contrib/Curated-Apps

3. User is expected to first have a base image `<base_image_with_pytorch>` ready with PyTorch and
   the necessary application files built into this image. The current directory contains sample
   dockerfiles and instructions to create a test PyTorch base image. This base image is then passed
   to the curation application `curate.py` as shown below.

4. To generate a preconfigured non-production test confidential compute image for PyTorch,  follow
   the below steps:
   1. Generate a sample PyTorch application image `pytorch-encrypted`:

          $ /bin/bash workloads/pytorch/base_image_helper/helper.sh

   2. Generate the test confidential compute image based on the `pytorch-encrypted` image  as shown 
      below:

          $ python3 ./curate.py pytorch pytorch-encrypted test

5. To generate a custom confidential compute image based on a user-provided PyTorch image, execute
   the following to launch an interactive setup script:

       $ python3 ./curate.py pytorch <base_image_with_pytorch>

## Run the confidential compute image for PyTorch

- This example was tested on a Standard_DC8s_v3 Azure VM.
- Follow the output of the `curate.py` script to run the generated Docker image(s).

## Contents
This sub-directory contains artifacts which help in creating curated GSC PyTorch image, as explained
below:

    .
    +-- pytorch-gsc.dockerfile.template   # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `pytorch-gsc.dockerfile` that
    |                                       includes user-provided inputs such as `ca.cert`
    |                                       file and command-line arguments into the graminized
    |                                       PyTorch image.
    +-- pytorch.manifest.template           # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing PyTorch images), that will be passed to
    |                                       GSC.
    +-- base_image_helper/                # `base_image_helper` directory contains artifacts which
    |                                       helps in generating a base image with encrypted files.
