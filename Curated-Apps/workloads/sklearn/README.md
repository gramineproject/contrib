# Gramine Curated Intel® extension for Scikit-learn
In the following two sections, we explain how a Docker image for the Scikit-learn can be built and
 how the image can be executed.
[Prerequisites](https://github.com/gramineproject/contrib/tree/master/Curated-Apps/README.md) for
both the phases are assumed to be met.

## Build a confidential compute image for Scikit-learn
Execute the below commands on the VM.

1. Clone the Gramine Contrib repository:

       $ git clone --depth 1 https://github.com/gramineproject/contrib.git

2. Move to the Curated-Apps folder:

       $ cd contrib/Curated-Apps

3. User is expected to first have a base image `<base_image_with_scikit-learn>` ready with
   Scikit-learn and the necessary application files built into this image. The current directory
   contains sample dockerfiles and instructions to create a test Scikit-learn base image. This base
   image is then passed to the curation application `curate.py` as shown below.

4. To generate a preconfigured non-production test `Intel® extension
   for Scikit-learn` confidential compute image, follow the below steps:
   1. Generate a sample Scikit-learn application image `sklearn-base`:

          $ /bin/bash workloads/sklearn/base_image_helper/helper.sh

   2. Generate the test confidential compute image based on the `sklearn-base` image  as shown
      below:

          $ python3 ./curate.py sklearn sklearn-base test

5. To generate a custom confidential compute image based on a user-provided Scikit-learn image,
   execute the following to launch an interactive setup script:

       $ python3 ./curate.py sklearn <base_image_with_scikit-learn>

## Run the confidential compute image for Scikit-learn

- This example was tested on a Standard_DC8s_v3 Azure VM.
- Follow the output of the `curate.py` script to run the generated Docker image(s).

## Contents
This sub-directory contains artifacts which help in creating curated GSC Scikit-learn image,
as explained below:

    .
    |-- sklearn-gsc.dockerfile.template   # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `sklearn-gsc.dockerfile` that
    |                                       includes user-provided inputs such as `ca.cert`
    |                                       file and command-line arguments into the graminized
    |                                       Scikit-learn image.
    |-- sklearn.manifest.template         # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing Scikit-learn images), that will be
    |                                       passed to GSC.
    |-- base_image_helper/                # `base_image_helper` directory contains artifacts which
    |                                       helps in generating a base image.

