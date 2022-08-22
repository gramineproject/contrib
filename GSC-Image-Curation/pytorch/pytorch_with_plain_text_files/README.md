## Please install the pre-requisites from the below link

https://github.com/gramineproject/examples/blob/master/pytorch/README.md#pre-requisites

These pre-requisites will download alexnet-pretrained.pt (which is more than 200MB file).

Once this file is downloaded , please save it to plaintext directory.

## Building pytorch plain image

`docker build -t <pytorch-plain> .`

once the image is created , please use `gsc_imae_creation/curation-script.sh` to create the <gsc-pytorch-plain> image
