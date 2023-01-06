This directory contains steps and artifacts to create a base docker image of Intel® extension
for Scikit-learn.

# Installing prerequisites

Please run the following command to install the required packages (Ubuntu-specific):

```sh
pip3 install --upgrade pip # on ubuntu 18.04 machine
python3 -m pip install scikit-learn-intelex pandas numpy
```

# Base docker image creation

Execute `bash ./helper.sh` command to create Scikit-learn base image.

Please refer to `Curated-Apps/workloads/sklearn/README.md` to curate the image created in above
steps with GSC.
