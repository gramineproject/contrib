# Intel® Confidential Compute for Scikit-learn

In the following two sections, we explain how a Docker image for a Gramine-protected Scikit-learn
version can be built and how the image can be executed. We assume that the
[prerequisites](../../README.md) for the build and the execution phase are met.


## Build a Gramine-protected Scikit-learn image

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
   build a Docker base image (`<base_image_with_scikit-learn>`) containing Scikit-learn and the
   necessary files.

   - To generate a Gramine-protected, pre-configured, non-production ready, test image for
     Scikit-learn, perform the following steps:

     1. Install the [prerequisites](base_image_helper/README.md) for this workload.

     2. Use the prepared helper script (`base_image_helper/helper.sh`) to generate a Scikit-learn
        Docker image:
        ```sh
        /bin/bash workloads/sklearn/base_image_helper/helper.sh
        ```
        The resulting Docker image is called `sklearn-base`.

     3. Generate Gramine-protected, pre-configured, non-production ready, test image for
        Scikit-learn, which is based on the just generated `sklearn-base` image:
        ```sh
        python3 ./curate.py sklearn sklearn-base --test
        ```
   - To generate a Gramine-protected, pre-configured Scikit-learn image based on a user-provided
     Scikit-learn Docker image, execute the following to launch an interactive setup script:
     ```sh
     python3 ./curate.py sklearn <base_image_with_scikit-learn>
     ```

## Execute Gramine-protected Scikit-learn image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC48ds_v3 Azure VM.


## Contents

This directory contains the following artifacts, which help to create a Gramine-protected
Scikit-learn image:

    .
    |-- sklearn-gsc.dockerfile.template   # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `sklearn-gsc.dockerfile` that
    |                                       includes user-provided inputs, e.g., `ca.cert` file etc.
    |                                       into the graminized Scikit-learn image.
    |-- sklearn.manifest.template         # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing Scikit-learn images) that will be
    |                                       passed to GSC.
    |-- base_image_helper/                # Directory contains artifacts that help to generate a
    |                                       base image.
