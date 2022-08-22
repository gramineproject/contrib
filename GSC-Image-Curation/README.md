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

`$ sudo python3 ./curate.py redis/redis:7.0.0 test`

To generate a custom image
`$ sudo python3 ./curate.py redis/<your image>`


(2) Pytorch

To generate a preconfigured test graminized image for pytorch:x dockerhub image

`$ sudo python3 ./curate.py pytorch/<pytorch_image> test`

To generate a custom image
`$ sudo python3 ./curate.py pytorch/<your image>`
