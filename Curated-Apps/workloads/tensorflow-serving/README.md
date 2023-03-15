# Gramine Curated tensorflow-serving
In the following two sections, we explain how a GSC image for the tensorflow-serving can be
built and how the image can be executed.
[Prerequisites](https://github.com/gramineproject/contrib/tree/master/Curated-Apps/README.md) for
both the phases are assumed to be met.

## Build a confidential compute image for tensorflow-serving
Execute the below commands on the VM.

1. Clone the Gramine Contrib repository and move to the Curated-Apps folder:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   cd contrib/Curated-Apps
   ```

2. User is expected to first have a base image `<base_image_with_tensorflow-serving>` ready with
   tensorflow-serving and the necessary application files built into this image. The
   directory `workloads/tensorflow-serving/base_image_helper` contains
   sample dockerfile and instructions to create a test tensorflow-serving
   base image. This base image is then passed to the curation application `curate.py` as shown
   below.

3. To generate a preconfigured non-production test confidential compute image for
   tensorflow-serving, follow the below steps:

   1. Generate a sample tensorflow-serving application image `tf-serving-base`:
      ```sh
      /bin/bash workloads/tensorflow-serving/base_image_helper/helper.sh
      ```

   2. Generate the test confidential compute image based on the `tf-serving-base` image as shown
      below. By default, ResNet is enabled. To enable other models you need to modify `model_name`
      and `model_base_path` in `workloads/tensorflow-serving/insecure_args.txt` file.
      ```sh
      python3 ./curate.py tensorflow-serving tf-serving-base test
      ```

4. Or, to generate a custom confidential compute image based on a user-provided tensorflow-serving
   image, execute the following to launch an interactive setup script. Please input command-line
   arguments `--model_name="resnet" --model_base_path="/models/resnet"` for resnet
   model, `--model_name="mnist" --model_base_path="/models/mnist"` for mnist model and
   `--model_name="half_plus_two" --model_base_path="/models/half_plus_two"` for half_plus_two
   model.
   ```sh
   python3 ./curate.py tensorflow-serving <base_image_with_tensorflow-serving>
   ```

## Run the confidential compute image for tensorflow-serving

- This example was tested on a Standard_DC48ds_v3 Azure VM.
- Follow the output of the `curate.py` script to run the generated Docker image(s).

## Contents
This sub-directory contains artifacts which help in creating curated GSC tensorflow-serving image,
as explained below:

    .
    |-- tensorflow-serving-gsc.dockerfile.template   # Template used by `curation_script.sh` to
    |                                                  create a wrapper dockerfile
    |                                                  `tensorflow-serving-gsc.dockerfile` that
    |                                                  includes user-provided inputs e.g. `ca.cert`
    |                                                  file etc. into the graminized MySQL image.
    |-- tensorflow-serving.manifest.template         # Template used by `curation_script.sh` to
    |                                                  create a user manifest file (with basic set
    |                                                  of values defined for graminizing
    |                                                  tensorflow-serving images), that will be
    |                                                  passed to GSC.
    |-- base_image_helper/                           # `base_image_helper` directory contains steps
    |                                                  which helps in generating a base image.
