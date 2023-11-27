# Intel® Confidential Compute for Memcached

In the following two sections, we explain how a Docker image for a Gramine-protected Memcached
version can be built and how the image can be executed. We assume that the
[prerequisites](../../README.md) for the build and the execution phase are met.

## Build a Gramine-protected Memcached image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```
2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```
3. Perform one of the following alternatives:
    - To generate a Gramine-protected, pre-configured, non-production ready, test image for
      Memcached, execute the following script:
      ```sh
      python3 ./curate.py memcached ubuntu/memcached:1.5-20.04_beta --test
      ```
    - To generate a Gramine-protected, pre-configured Memcached image based on a user-provided
      Memcached image, execute the following to launch an interactive setup script:
      ```sh
      python3 ./curate.py memcached <your_image>
      ```

## Execute Gramine-protected Memcached image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC8s_v3 Azure VM.


## Contents

This directory contains the following artifacts, which help to create a Gramine-protected Memcached
image:

    .
    |-- memcached-gsc.dockerfile.template    # Template used by `curation_script.sh` to create a
    |                                          wrapper dockerfile `memcached-gsc.dockerfile` that
    |                                          includes user-provided inputs, e.g., `ca.cert` file
    |                                          etc. into the graminized Memcached image.
    |-- memcached.manifest.template          # Template used by `curation_script.sh` to create a
    |                                          user manifest file (with basic set of values defined
    |                                          for graminizing Memcached images) that will be
    |                                          passed to GSC.
