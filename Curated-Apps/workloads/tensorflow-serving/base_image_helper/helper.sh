# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# exit when any command fails
set -e

if [ ! -d serving ]; then
    git clone https://github.com/tensorflow/serving.git
fi

export TF_SERVING_ROOT=$(pwd)/serving
export TF_SERVING_AZ_IMAGE_UBUNTU_20="gramine.azurecr.io:443/base_images/intel-tensorflow-ubuntu20.04"
export TF_SERVING_AZ_IMAGE_UBUNTU_18="gramine.azurecr.io:443/base_images/intel-tensorflow-ubuntu18.04"
export TF_SERVING_IMAGE_FINAL=intel/intel-optimized-tensorflow-serving:2.9.1-ubuntu

OS=$1
if [ "$OS" == "20.04" ]
then  
    sed -i "1s|.*|FROM ${TF_SERVING_AZ_IMAGE_UBUNTU_20} |" workloads/tensorflow-serving/base_image_helper/Dockerfile
elif [ "$OS" == "18.04" ]
then
    sed -i "1s|.*|FROM ${TF_SERVING_AZ_IMAGE_UBUNTU_18} |" workloads/tensorflow-serving/base_image_helper/Dockerfile
else
    echo "Not valid option."
    exit
fi

pushd workloads/tensorflow-serving/base_image_helper

if [ -d /tmp/resnet ]; then
    rm -rf /tmp/resnet
fi
mkdir -p /tmp/resnet
curl -s http://download.tensorflow.org/models/official/20181001_resnet/savedmodels/resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz \
| tar --strip-components=2 -C /tmp/resnet -xvz
if [ -d models ]; then
    rm -rf models
fi
mkdir -p models
mv /tmp/resnet models/resnet

if [ -d /tmp/mnist ]; then
    rm -rf /tmp/mnist
fi
pushd ${TF_SERVING_ROOT}
tools/run_in_docker.sh python tensorflow_serving/example/mnist_saved_model.py /tmp/mnist
popd
mv /tmp/mnist models/mnist

docker build \
    -f Dockerfile \
    -t ${TF_SERVING_IMAGE_FINAL} .
popd

echo -e '\n\nCreated base image `'$TF_SERVING_IMAGE_FINAL'`.'
echo -e 'Please refer to `Curated-Apps/workloads/tensorflow-serving/README.md` to curate the above image' \
' with GSC.\n'
