# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# exit when any command fails
set -e
CUR_DIR=$(pwd)
MY_PATH=$(dirname "$0")
cd $MY_PATH

if [ ! -d serving ]; then
    git clone https://github.com/tensorflow/serving.git
fi

export TF_SERVING_ROOT=$(pwd)/serving
export TF_SERVING_AZ_IMAGE_UBUNTU_20="gramine.azurecr.io:443/base_images/intel-optimized-tensorflow-serving-avx512-ubuntu20.04"
export TF_SERVING_AZ_IMAGE_UBUNTU_18="gramine.azurecr.io:443/base_images/intel-optimized-tensorflow-serving-avx512-ubuntu18.04"
export TF_SERVING_IMAGE_FINAL=tf-serving-base

OS=$1
if [ "$OS" == "20.04" ]
then  
    sed -i "1s|.*|FROM ${TF_SERVING_AZ_IMAGE_UBUNTU_20} |" Dockerfile
elif [ "$OS" == "18.04" ]
then
    sed -i "1s|.*|FROM ${TF_SERVING_AZ_IMAGE_UBUNTU_18} |" Dockerfile
else
    echo "No Ubuntu version provided."
    echo "Allowed usage:"
    echo "/bin/bash helper.sh 20.04"
    echo "/bin/bash helper.sh 18.04"
    exit
fi

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

mkdir models/half_plus_two
cp -r $TF_SERVING_ROOT/tensorflow_serving/servables/tensorflow/testdata/saved_model_half_plus_two_mkl/* models/half_plus_two

docker build \
    -f Dockerfile \
    -t ${TF_SERVING_IMAGE_FINAL} .

cd $CUR_DIR

echo -e '\n\nCreated base image `'$TF_SERVING_IMAGE_FINAL'`.'
echo -e 'Please refer to `Curated-Apps/workloads/tensorflow-serving/README.md` to curate the above image' \
' with GSC.\n'
