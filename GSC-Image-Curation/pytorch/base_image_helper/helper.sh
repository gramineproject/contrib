
image_name="pytorch-base"
git clone --depth 1 https://github.com/gramineproject/examples.git
cd examples/pytorch

# download and save the pre-trained model
python3 download-pretrained-model.py

# encrypt files using given encryption key in file `wrap-key`
if [[ "$1" == "encrypt" ]]; then
    cd ../../
    gramine-sgx-pf-crypt encrypt -w wrap-key -i examples/pytorch/input.jpg -o input.jpg
    gramine-sgx-pf-crypt encrypt -w wrap-key -i examples/pytorch/classes.txt -o classes.txt
    gramine-sgx-pf-crypt encrypt -w wrap-key -i examples/pytorch/alexnet-pretrained.pt -o alexnet-pretrained.pt
    mv examples/pytorch/pytorchexample.py ./
    image_name="pytorch-base-"$1
else
    mv input.jpg classes.txt alexnet-pretrained.pt pytorchexample.py ../../
    cd ../../
fi

rm -rf examples

# build base image
docker rmi -f $image_name >/dev/null 2>&1
docker build -t $image_name .

echo -e "\n\nCreated base image \`$image_name\`."
echo -e "Please refer \`GSC-Image-Curation/README.md\` to curate the above image with GSC.\n"
