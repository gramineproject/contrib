# Gramine Curated PyTorch
In the following two sections, we explain how a Docker image for the protected PyTorch version can
be built and how the image can be executed.
[Prerequisites](https://github.com/gramineproject/contrib/tree/master/Curated-Apps/README.md) for
both the phases are assumed to be met.

## Build a confidential compute image for PyTorch
Execute the below commands on your system.

1. Clone the Gramine Contrib repository and move to the Curated-Apps folder:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   cd contrib/Curated-Apps
   ```

2. User is expected to first have a base image `<base_image_with_pytorch>` ready with PyTorch and
   the necessary application files built into this image. The current directory contains sample
   dockerfiles and instructions to create a test PyTorch base image. This base image is then passed
   to the curation application `curate.py` as shown below.

3. To generate and run preconfigured non-production test confidential compute image for PyTorch,
   follow the below steps:

   1. Install prerequisites given [here](https://github.com/gramineproject/contrib/blob/master/Curated-Apps/workloads/pytorch/base_image_helper/README.md#prerequisites) for creating sample PyTorch application image with encrypted files

   2. Generate a sample PyTorch application image `pytorch-encrypted`:
      ```sh
      /bin/bash workloads/pytorch/base_image_helper/helper.sh
      ```
      The above `helper.sh` script encrypts sensitive files such as models, data etc. with an auto
      generated test encryption key `workloads/pytorch/base_image_helper/encryption_key` and copies
      to the base image. Learn more about [Encrypted files](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files) support in Gramine.

   3. Generate the test confidential compute image based on the `pytorch-encrypted` image as shown
      below:
      ```sh
      python3 ./curate.py pytorch pytorch-encrypted test
      ```

   4. Run test confidential compute image for PyTorch using below command:
      ```sh
      docker run --net=host --device=/dev/sgx/enclave -it gsc-pytorch-encrypted
      ```

   5. Follow the instructions [here](https://github.com/gramineproject/contrib/blob/master/Curated-Apps/workloads/pytorch/base_image_helper/README.md#retrieve-and-decrypt-results) to retrieve the results.

4. Or, to generate a custom confidential compute image based on a user-provided PyTorch image,
   execute the following to launch an interactive setup script:
   ```sh
   python3 ./curate.py pytorch <base_image_with_pytorch>
   ```

## Run the confidential compute image for PyTorch

- This example was tested on a Standard_DC8s_v3 Azure VM.
- Follow the output of the `curate.py` script to run the generated Docker image(s).

## Contents
This sub-directory contains artifacts which help in creating curated GSC PyTorch image, as explained
below:

    .
    |-- pytorch-gsc.dockerfile.template   # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `pytorch-gsc.dockerfile` that
    |                                       includes user-provided inputs e.g. `ca.cert` file etc.
    |                                       into the graminized PyTorch image.
    |-- pytorch.manifest.template         # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing PyTorch images), that will be passed to
    |                                       GSC.
    |-- base_image_helper/                # `base_image_helper` directory contains artifacts which
    |                                       helps in generating a base image with encrypted files.
