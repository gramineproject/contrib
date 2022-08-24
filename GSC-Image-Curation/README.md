# Curate your own Gramine Shielded Container image

This guide demonstrates how one can transform any container image to a graminized one, packing
features such as attestation and beyond, necessary for enabling end to end usescases securely.
A list of examples are provided below for reference. One can easily extend these reference examples
to supporting more workloads by inspecting the contents of any of the reference workloads
(for e.g. /redis/).

## Prerequisites

```sh
$ sudo apt-get install jq

$ sudo apt-get install docker.io python3 python3-pip

$ pip3 install docker jinja2 toml pyyaml
```

## Sample Workloads

(1) Redis

Want to genenerate a preconfigured test graminized image for redis:7.0.0 dockerhub image? All you
need to do is execute the gsc curation script as given below. At the end of the curation, the script
will also advise how to run the graminized image with docker.

To generate a preconfigured test graminized image

`$ sudo python3 ./curate.py redis/redis:7.0.0 test`

To generate a custom graminized image, follow the below. This will launch an interactive application
that will take inputs to create a curated graminized image.

`$ sudo python3 ./curate.py redis/<your image>`


(2) Pytorch

User is expected to first have his base image `<base_image_with_pytorch>` ready with PyTorch and
the necessary application files built into this image. This base image is then passed to the
curation application `curate.py` as shown below.

To generate a preconfigured test graminized image

`$ sudo python3 ./curate.py pytorch/<base_image_with_pytorch> test`

To generate a custom graminized image, follow the below. This will launch an interactive application
that will take inputs to create a curated graminized image.

`$ sudo python3 ./curate.py pytorch/<base_image_with_pytorch>`
