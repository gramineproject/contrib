# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# exit when any command fails
set -e

CUR_DIR=$(pwd)
MY_PATH=$(dirname "$0")
cd $MY_PATH

image_name='sklearn-base'

echo "Downloading datasets..."

# Download and save the datasets
python3 download_dataset.py

# Build Scikit-learn base image
echo "Base image creation started"
docker rmi -f $image_name >/dev/null 2>&1
docker build -t $image_name .

cd $CUR_DIR

echo -e '\n\nCreated base image `'$image_name'`.'
echo -e 'Please refer to `Intel-Confidential-Compute-for-X/workloads/sklearn/README.md` to ' \
'generate a Gramine-protected version of this Docker image.\n'
