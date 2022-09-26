# Gramine Curated Redis
In the following two sections, we explain how a Docker image for the protected Redis version can be
build and how the image can be executed.

## Build a confidential compute image for Redis
The following description assumes that the [prerequisites](https://github.com/gramineproject/contrib.git/Curated-Apps/README.md)
for building the curated image are met, and the commands below are executed on the
corresponding VM.

1. Clone the Gramine Contrib repository
   `$ git clone https://github.com/gramineproject/contrib.git`

2. Move to the Curated-Apps folder
   `$ cd contrib/Curated-Apps`

3. To generate a preconfigured confidential compute image for redis, execute the following script:
   `$ python3 ./curate.py redis redis:7.0.0 test`

4. To generate a custom confidential compute image based on a user-provided Redis image, execute
   the following to launch an interactive setup script:
   `$ python3 ./curate.py redis <your_image>`

## Run the confidential compute image for Redis
The following description assumes that the [prerequisites](https://github.com/gramineproject/contrib.git/Curated-Apps/README.md)
for running the curated image are met

- Follow the output of the image build script `curate.py` to run the generated Docker image
- The test example used here was tested on a Standard_DC2s_v2 Azure VM.

## Contents
This sub-directory contains artifacts which help in creating curated GSC Redis image, as explained
below:

    .
    +-- redis-gsc.dockerfile.template      # Template used by `curation_script.sh` to create a
    |                                        wrapper dockerfile `redis-gsc.dockerfile` that
    |                                        dockerfile `redis-gsc.dockerfile` that includes
    |                                        user-provided inputs such as `ca.cert` file and
    |                                        run-time arguments into the graminized Redis image.
    +-- redis.manifest.template            # Template used by `curation_script.sh` to create a
    |                                        user manifest file (with basic set of values defined
    |                                        for graminizing Redis images), that will be passed to
    |                                        GSC.
