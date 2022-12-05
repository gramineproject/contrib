This directory contains steps to create a docker image based on different ubuntu versions.

# Base docker image creation

- cd `contrib/Curated-Apps`
 
- Execute `/bin/bash workloads/tensorflow-serving/base_image_helper/helper.sh 20.04` to create base
image for ubuntu 20.04

- Execute `/bin/bash workloads/tensorflow-serving/base_image_helper/helper.sh 18.04` to create base
image for ubuntu 18.04

Please refer to `Curated-Apps/workloads/tensorflow-serving/README.md` to curate the image created
in above steps with GSC.
