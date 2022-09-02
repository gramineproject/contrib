This directory contains artifacts which helps in creating curated GSC Redis image, as explained
below:

- `redis-gsc.dockerfile.template` file is used by `curation_script.sh` to create a wrapper
  dockerfile `redis-gsc.dockerfile` that includes user provided inputs such as `ca.cert`
  file and run-time arguments into the graminized Redis image.

- `redis.manifest.template` file have basic set of values defined for graminizing Redis images.
  This manifest template is used by `curation_script.sh` to create the user manifest file that
  will be passed to GSC.
