This directory contains steps and artifacts to create a Scikit-learn Docker image.


# Prerequisites

- Install dependencies:
    - Ubuntu 18.04:
        ```sh
        python3 -m pip install --upgrade pip # on ubuntu 18.04 machine
        python3 -m pip install scikit-learn-intelex pandas numpy
        ```


# Create base Docker image

Execute the helper script contained in this directory: `./helper.sh`.

This script downloads a test dataset and builds a Scikit-learn Docker image.

Please refer to the [README of Intel® Confidential Compute for Scikit-learn](../README.md)
to generate a Gramine-protected version of this Docker image.
