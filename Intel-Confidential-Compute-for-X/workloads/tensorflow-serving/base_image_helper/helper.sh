# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# exit when any command fails
set -e
MY_PATH=$(dirname "$0")
pushd ${MY_PATH}

if [ ! -d serving ]; then
    git clone https://github.com/tensorflow/serving.git
fi

export TF_SERVING_ROOT=$(pwd)/serving
export TF_SERVING_IMAGE_FINAL=tf-serving-base

if [ -d /tmp/resnet ]; then
    rm -rf /tmp/resnet
fi
mkdir -p /tmp/resnet
resnet_checksum=c2c94887e54f8427716569385bc055d9e12e1608e8c65247fa5297d3f5ddc1bc
if [ ! -f resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz ]; then
    wget http://download.tensorflow.org/models/official/20181001_resnet/savedmodels/resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz || exit
    sha256sum resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz > hash_resnet.txt
    grep $resnet_checksum hash_resnet.txt
    if [ $? -ne 0 ]; then
        echo "File resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz checksum failure"
        rm -f resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz
        exit
    fi
fi
tar --strip-components=2 -C /tmp/resnet -xvzf resnet_v1_fp32_savedmodel_NCHW_jpg.tar.gz

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

popd

echo -e '\n\nCreated base image `'$TF_SERVING_IMAGE_FINAL'`.'
echo -e 'Please refer to `Intel-Confidential-Compute-for-X/workloads/tensorflow-serving/README.md` to curate the above image' \
' with GSC.\n'
