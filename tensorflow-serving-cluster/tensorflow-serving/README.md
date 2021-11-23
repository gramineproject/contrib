# TensorFlow Serving
[TensorFlow Serving](https://www.TensorFlow.org/tfx/guide/serving) is a flexible,
high-performance serving system for machine learning models. Here we choose it as
our AI service.

This directory contains:
- `client` sub-directory.
  It contains scripts of client. The user can send the request from the client
  with script `resnet_client_grpc.py`.
- `docker` sub-directory.
  It contains the script `build_gramine_tf_serving_image.sh` to build TensorFlow
  Serving docker image.
- `kubernetes` sub-directory.
  It contains the Yaml configuration files in Kubernetes which are used for
  TensorFlow Serving elastic deployment.
- other scripts:
  - `download_model.sh` to download the model file.
  - `model_graph_to_saved_model.py` to convert the model file.
  - `run_gramine_tf_serving.sh` and `run_tf_serving.sh` to run TensorFlow Serving
  with Gramine and natively (without Gramine).
  - `generate_ssh_config.sh` to generate SSL/TLS certificate and key between TensorFlow
  Serving and client.

In the tutorial, we describe the usage of these scripts and command, please follow
the tutorial to execute the provided scripts step by step.
