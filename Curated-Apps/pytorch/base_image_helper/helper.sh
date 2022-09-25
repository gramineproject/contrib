# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

image_name="pytorch-encrypted"
git clone --depth 1 https://github.com/gramineproject/examples.git
cd examples/pytorch

# Download and save the pre-trained model
python3 download-pretrained-model.py
cd ../../

# Encrypt files using given encryption key in file `wrap_key`
gramine-sgx-pf-crypt encrypt -w wrap_key -i examples/pytorch/input.jpg -o input.jpg
gramine-sgx-pf-crypt encrypt -w wrap_key -i examples/pytorch/classes.txt -o classes.txt
gramine-sgx-pf-crypt encrypt -w wrap_key -i examples/pytorch/alexnet-pretrained.pt -o alexnet-pretrained.pt

mv examples/pytorch/pytorchexample.py ./
rm -rf examples

# Build pytorch base image
docker rmi -f $image_name >/dev/null 2>&1
docker build -t $image_name .

echo -e "\n\nCreated base image \`$image_name\`."
echo -e "Please refer \`Curated-Apps/README.md\` to curate the above image with GSC.\n"
