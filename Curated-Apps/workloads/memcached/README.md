# Gramine Curated Memcached

In the following two sections, we explain how a Docker image for the protected Memcached version
can be built and how the image can be executed.
[Prerequisites](https://github.com/gramineproject/contrib/tree/master/Curated-Apps/README.md) for
both the phases are assumed to be met.

## Build a confidential compute image for Memcached

Execute the below commands on your system.

1. Clone the Gramine Contrib repository:

       $ git clone --depth 1 https://github.com/gramineproject/contrib.git

2. Move to the Curated-Apps folder:

       $ cd contrib/Curated-Apps

3. To generate a preconfigured non-production test confidential compute image for Memcached,
   execute the following script:

       $ python3 ./curate.py memcached ubuntu/memcached:1.5-20.04_beta test

4. Or, to generate a custom confidential compute image based on a user-provided Memcached image,
   execute the following to launch an interactive setup script:

       $ python3 ./curate.py memcached <your_image>

## Run the confidential compute image for Memcached

- This example was tested on a Standard_DC8ds_v3 Azure VM.
- Follow the output of the image build script `curate.py` to run the generated Docker image.

## Contents

This sub-directory contains artifacts which help in creating curated GSC Memcached image, as
explained below:

    .
    |-- memcached-gsc.dockerfile.template    # Template used by `curation_script.sh` to create a
    |                                          wrapper dockerfile `memcached-gsc.dockerfile` that
    |                                          includes user-provided inputs e.g. `ca.cert` file
    |                                          etc. into the graminized Memcached image.
    |-- memcached.manifest.template          # Template used by `curation_script.sh` to create a
    |                                          user manifest file (with basic set of values defined
    |                                          for graminizing Memcached images), that will be
    |                                          passed to GSC.
