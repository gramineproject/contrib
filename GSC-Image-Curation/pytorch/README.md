This directory contains artifacts which helps in creating curated GSC PyTorch image, as explained below:

- `pytorch-gsc.dockerfile.template` file is used by `curation_script.sh` to create a wrapper dockerfile `pytorch-gsc.dockerfile`
 that includes user provided inputs such as `ca.cert` file and run-time arguments into the graminized PyTorch image.

- `pytorch.manifest.template` file have basic set of values defined for graminizing PyTorch images. This manifest template
 is used by `curation_script.sh` to create the user manifest file that will be passed to GSC.

- `base_image_helper` directory contains artifacts which helps in generating a base image with
 plaintext or encrypted files.
