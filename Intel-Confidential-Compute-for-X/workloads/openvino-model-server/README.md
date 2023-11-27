# Intel® Confidential Compute for OpenVINO Model Server

In the following two sections, we explain how a Docker image for a Gramine-protected OpenVINO Model
Server version can be built and how the image can be executed. We assume that the
[prerequisites](../../README.md) for the build and the execution phase are met.


## Build a Gramine-protected OpenVINO Model Server image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```

2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```

3. Download model:
   Store components of the model in the `workloads/openvino-model-server/models/1` directory.
   Follow below step to download face-detection model for test purpose.

   ```
   mkdir workloads/openvino-model-server/models
   curl --create-dirs https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/face-detection-retail-0004/FP32/face-detection-retail-0004.xml https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/face-detection-retail-0004/FP32/face-detection-retail-0004.bin -o workloads/openvino-model-server/models/1/face-detection-retail-0004.xml -o workloads/openvino-model-server/models/1/face-detection-retail-0004.bin
   ```

4. Encrypting model:

    1. [Install Gramine](https://gramine.readthedocs.io/en/stable/installation.html)
        as the encryption is done using the `gramine-sgx-pf-crypt` tool which is part of Gramine
        installation.

    2. Use the `gramine-sgx-pf-crypt` tool to encrypt the test model
       `workloads/openvino-model-server/models`. The encrypted model will be stored in the
       `model_encrypted` directory under the newly created `tmpfs` mount point `/mnt/tmpfs`.
       ```sh
       sudo mkdir -p /mnt/tmpfs
       sudo mount -t tmpfs tmpfs /mnt/tmpfs
       mkdir /mnt/tmpfs/model_encrypted

       dd if=/dev/urandom bs=16 count=1 > workloads/openvino-model-server/base_image_helper/encryption_key
       gramine-sgx-pf-crypt encrypt \
           -w workloads/openvino-model-server/base_image_helper/encryption_key \
           -i workloads/openvino-model-server/models -o /mnt/tmpfs/model_encrypted
       ```
       You can learn more about Gramine's support of encrypted files in the
       [corresponding documentation](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files).

5. Perform one of the following alternatives:

    1. To generate a Gramine-protected, pre-configured, non-production ready, test image for
      OpenVINO Model Server, execute the following script:
      ```sh
      python3 ./curate.py openvino-model-server openvino/model_server:2023.0 --test
      ```

    2. To generate a Gramine-protected, pre-configured OpenVINO Model Server image based on a
      user-provided OpenVINO Model Server image, execute the following to launch an interactive
      setup script:
      ```sh
      python3 ./curate.py openvino-model-server <your_image>
      ```

      Please provide the following inputs to the script:
      - `--model_path <abs_path_to_encrypted_model> --model_name face-detection --port 9000
        --shape auto` when prompted for command-line arguments.
      - `-u $(id -u):$(id -g) -p 9000:9000
        -v <abs_path_to_encrypted_model>:<abs_path_to_encrypted_model>` when prompted for
        additional docker flags.
      - `<abs_path_to_encrypted_model>` and `<encryption_key>` when prompted for encrypted
        files and encryption key respectively.

## Execute Gramine-protected OpenVINO Model Server image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC8s_v3 Azure VM.


## Run inference on the test image

- Move to `workloads/openvino-model-server` folder:
   ```sh
   cd workloads/openvino-model-server
   ```

- Prepare the example client components:
  ```sh
  curl https://raw.githubusercontent.com/openvinotoolkit/model_server/releases/2023/0/demos/common/python/client_utils.py -o client_utils.py
  curl https://raw.githubusercontent.com/openvinotoolkit/model_server/releases/2023/0/demos/face_detection/python/face_detection.py -o face_detection.py
  ```

- Download data for inference:
  ```sh
  curl --create-dirs https://raw.githubusercontent.com/openvinotoolkit/model_server/releases/2023/0/demos/common/static/images/people/people1.jpeg -o images/people1.jpeg
  ```

- Trigger inference run in the GSC OpenVINO Model Server from a Python client:
  ```sh
  python3 -m venv env
  source env/bin/activate
  pip install --upgrade pip
  pip install -r client_requirements.txt

  mkdir results

  # if you are behind a corporate proxy, export no_proxy envvar to avoid Python failure below
  # "UNKNOWN:failed to connect to all addresses;..."
  python3 face_detection.py --batch_size 1 --width 600 --height 400 --input_images_dir images \
      --output_dir results --grpc_port 9000

  deactivate
  ```

## Contents

This directory contains the following artifacts, which help to create a Gramine-protected OpenVINO
Model Server image:

    .
    |-- openvino-model-server-gsc.dockerfile.template     # Template used by `curation_script.sh`
    |                                                       to create a wrapper dockerfile
    |                                                       `openvino-model-server-gsc.dockerfile`
    |                                                       that includes user-provided inputs,
    |                                                       e.g., `ca.cert` file etc. into the
    |                                                       graminized OpenVINO Model Server image.
    |-- openvino-model-server.manifest.template           # Template used by `curation_script.sh`
    |                                                       to create a user manifest file (with
    |                                                       basic set of values defined for
    |                                                       graminizing OpenVINO Model Server
    |                                                       images) that will be passed to GSC.
    |-- base_image_helper/                                # This directory contains
    |                                                       `encrypted_files.txt` which contains
    |                                                       encrypted model directory required for
    |                                                       running the test OpenVINO Model Server
    |                                                       image.
    |-- docker_run_flags.txt                              # This file contains docker run flags
    |                                                       required for running the test OpenVINO
    |                                                       Model Server image.
    |-- insecure_args.txt                                 # This file contains command line
    |                                                       arguments required for running the test
    |                                                       OpenVINO Model Server image.
    |-- client_requirements.txt                           # This file contains all dependencies
    |                                                       that need to be installed to run
    |                                                       inference.
