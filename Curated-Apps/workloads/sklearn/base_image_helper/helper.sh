# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# exit when any command fails
set -e

CUR_DIR=$(pwd)
MY_PATH=$(dirname "$0")
cd $MY_PATH

image_name='sklearn-base'

# Build Scikit-learn base image
docker rmi -f $image_name >/dev/null 2>&1
docker build -t $image_name .

cd $CUR_DIR

echo -e '\n\nCreated base image `'$image_name'`.'
echo -e 'Please refer to `Curated-Apps/workloads/sklearn/README.md` to curate the above image' \
' with GSC.\n'
