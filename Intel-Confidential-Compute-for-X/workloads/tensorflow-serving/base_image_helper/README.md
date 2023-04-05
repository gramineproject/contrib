This directory contains steps and artifacts to create a Tensorflow Serving Docker image.


# Create base Docker image

Execute the helper script contained in this directory: `./helper.sh`.

This script clones the [TensorFlow Serving repository](https://github.com/tensorflow/serving.git),
downloads a model, and builds a Docker image containing Tensorflow Serving and the model.

Please refer to the [README of Intel® Confidential Compute for TensorFlow Serving](../README.md)
to generate a Gramine-protected version of this Docker image.
