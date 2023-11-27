# Intel® Confidential Compute for TensorFlow Serving

In the following two sections, we explain how a Docker image for a Gramine-protected TensorFlow
Serving version can be built and how the image can be executed. We assume that the
[prerequisites](../../README.md) for the build and the execution phase are met.


## Build a Gramine-protected TensorFlow Serving image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```

2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```

3. Perform one of the following alternatives. Note that both alternatives assume that the user has
   build a Docker base image (`<base_image_with_tensorflow-serving>`) containing TensorFlow Serving
   and the necessary application files.

   - To generate a Gramine-protected, pre-configured, non-production ready, test image for
     TensorFlow Serving, perform the following steps:

     1. Use the prepared helper script (`base_image_helper/helper.sh`) to generate a TensorFlow
        Serving Docker image:
        ```sh
        /bin/bash workloads/tensorflow-serving/base_image_helper/helper.sh
        ```
        The resulting Docker image is called `tf-serving-base`.

     2. Generate Gramine-protected, pre-configured, non-production ready, test image for TensorFlow
        Serving, which is based on the just generated `tf-serving-base` image. By default, ResNet is
        enabled, but you can easily change the model as shown below in the "Prepared Models"
        section.
        ```sh
        python3 ./curate.py tensorflow-serving tf-serving-base --test
        ```

   - To generate a Gramine-protected, pre-configured TensorFlow Serving image based on a
     user-provided TensorFlow Serving Docker image, execute the following to launch an interactive
     setup script. To select the model that should be used, use the command line arguments described
     below in the "Prepared Models" section.
     ```sh
     python3 ./curate.py tensorflow-serving <base_image_with_tensorflow-serving>
     ```


## Prepared Models

Currently, the following models can be used by just adjusting the `model_name` and `model_base_path`
parameters in the `workloads/tensorflow-serving/insecure_args.txt` file.
- ResNet: `--model_name="resnet" --model_base_path="/models/resnet"`
- MNIST: `--model_name="mnist" --model_base_path="/models/mnist"`
- half_plus_two: `--model_name="half_plus_two" --model_base_path="/models/half_plus_two"`


## Execute Gramine-protected TensorFlow Serving image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC48ds_v3 Azure VM.


## Contents

This directory contains the following artifacts, which help to create a Gramine-protected TensorFlow
Serving image:

    .
    |-- tensorflow-serving-gsc.dockerfile.template  # Template used by `curation_script.sh` to
    |                                                 create a wrapper dockerfile
    |                                                 `tensorflow-serving-gsc.dockerfile` that
    |                                                 includes user-provided inputs, e.g., `ca.cert`
    |                                                 file etc. into the graminized
    |                                                 TensorFlow Serving image.
    |-- tensorflow-serving.manifest.template        # Template used by `curation_script.sh` to
    |                                                 create a user manifest file (with basic set
    |                                                 of values defined for graminizing
    |                                                 TensorFlow Serving images) that will be
    |                                                 passed to GSC.
    |-- base_image_helper/                          # Directory contains artifacts that help to
    |                                                 generate a base image.
