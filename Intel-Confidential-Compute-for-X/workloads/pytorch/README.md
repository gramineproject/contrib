# Intel® Confidential Compute for PyTorch

In the following two sections, we explain how a Docker image for a Gramine-protected PyTorch version
can be built and how the image can be executed. We assume that the [prerequisites](../../README.md)
for the build and the execution phase are met.


## Build a Gramine-protected PyTorch image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```

2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```

3. Perform one of the following alternatives.  Note that both alternatives assume that the user has
   build a Docker base image (`<base_image_with_pytorch>`) containing PyTorch and the necessary
   files.

   - To generate a Gramine-protected, pre-configured, non-production ready, test image for PyTorch,
     perform the following steps:

     1. Install the [prerequisites](base_image_helper/README.md#prerequisites) for this workload.

     2. Use the prepared helper script (`base_image_helper/helper.sh`) to generate a PyTorch Docker
        image containing an encrypted model and an encrypted sample picture:
        ```sh
        /bin/bash workloads/pytorch/base_image_helper/helper.sh
        ```
        The resulting Docker image is called `pytorch-encrypted`.

     3. Generate Gramine-protected, pre-configured, non-production ready, test image for PyTorch,
        which is based on the just generated `pytorch-encrypted` image:
        ```sh
        python3 ./curate.py pytorch pytorch-encrypted --test
        ```

     4. Run the generated PyTorch image using below command:
        ```sh
        docker run --net=host --device=/dev/sgx/enclave -it gsc-pytorch-encrypted
        ```

   - To generate a Gramine-protected, pre-configured PyTorch image based on a user-provided PyTorch
     Docker image, execute the following to launch an interactive setup script:
     ```sh
     python3 ./curate.py pytorch <base_image_with_pytorch>
     ```


## Execute Gramine-protected PyTorch image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC8s_v3 Azure VM.


## Retrieve and decrypt the results

The encrypted results of the execution are generated in `/workspace/result.txt` within the
container. You need to copy the results from the container to your local machine and decrypt the
results using the following commands:
```sh
docker cp <container id or name>:/workspace/result.txt .
gramine-sgx-pf-crypt decrypt -w encryption_key -i result.txt -o result_plaintext.txt
```

Make sure that the path to your `encryption_key` is correct.


## Contents

This directory contains the following artifacts, which help to create a Gramine-protected PyTorch
image:

    .
    |-- pytorch-gsc.dockerfile.template   # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `pytorch-gsc.dockerfile` that
    |                                       includes user-provided inputs, e.g., `ca.cert` file etc.
    |                                       into the graminized PyTorch image.
    |-- pytorch.manifest.template         # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing PyTorch images) that will be passed to
    |                                       GSC.
    |-- base_image_helper/                # Directory contains artifacts that help to generate a
    |                                       base image containing an encrypted model and an
    |                                       encrypted sample picture.
