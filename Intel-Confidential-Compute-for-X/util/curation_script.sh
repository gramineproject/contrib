#!/bin/bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# This script takes input from curate.py and creates GSC image.
# The script can be called either for creating a non-production test image or a custom GSC image.
#
# The test image is created when user runs `python ./curate.py <workload type> <user_image> test`
# command. The image hence created will be signed with a test enclave key, and will not support
# attestation.
#
# In case of test image, the script takes 7 input parameters, whereas in case of custom image 13
# parameters are passed from curate.py.
#
# curate.py calls this script after taking all the user inputs. This script does not interact with
# user, it just processes the input received from curate.py and produces the final GSC image.

# The input parameters in sequence are below:
# -- arg1    : workload type (see workload/ sub-directory for list of supported workload types)
#              e.g. redis
# -- arg2    : base_image_name e.g. name of the base image to be graminized
# -- arg3    : distro e.g. ubuntu:18.04 or ubuntu:20.04
# -- arg4    : path to the enclave signing key or
#              'test' string to generate test signing key
# -- arg5    : CMD instruction for Dockerfile having all the command-line arguments
# -- arg6    : 'test-image' string to create a non-production GSC image when curate.py is run in
#            :  test mode
#            : y or n (attestation required?) in case of custom image creation
# -- arg7    : buildtype, valid values are release, debug and debugoptimized
# -- arg8    : verifier's ca certificate path
# -- arg9    : y or n (environment variables available?)
# -- arg10   : Actual environment variable string
# -- arg11   : y or n (encrypted files to be used with workload?)
# -- arg12   : Path to the encrypted files in the image
# -- arg13   : encryption key used for encrypting sensitive files such as models, data etc.
# -- arg14   : Passphrase to the enclave signing key (if applicable)

set -e

echo printing args $0 $@

workload_type=$1
wrapper_dockerfile=$workload_type'-gsc.dockerfile'
app_image_manifest=$workload_type'.manifest'

CUR_DIR=$(pwd)
WORKLOAD_DIR=$CUR_DIR'/workloads/'$workload_type
cd $WORKLOAD_DIR
rm -rf $CUR_DIR'/test' && mkdir $CUR_DIR'/test' >/dev/null 2>&1

cp -f $wrapper_dockerfile'.template' $wrapper_dockerfile
cp -f $app_image_manifest'.template' $app_image_manifest

base_image="$2"
distro="$3"
# Set base image name in the dockerfile
sed -i 's|^FROM <base_image_name>$|FROM '$base_image'|' $wrapper_dockerfile

if [[ "$base_image" == *":"* ]]; then
    app_image_x=$(echo $base_image | sed "s/:/_x:/")
else
    app_image_x="${base_image}_x"
fi

# Delete existing GSC image for the base image
docker rmi -f gsc-$base_image >/dev/null 2>&1

copy_cert_files=''
create_base_wrapper_image () {
    sed -i "s|<copy_cert_files>|$copy_cert_files|" $wrapper_dockerfile
    docker rmi -f $app_image_x >/dev/null 2>&1
    docker build -f $wrapper_dockerfile -t $app_image_x .
}

add_encrypted_files_to_manifest() {
    if [[ -z "$1" ]]; then
        return
    fi

    IFS=':' # Setting colon as delimiter
    read -a ef_files_list <<<"$1"
    unset IFS
    workdir_base_image="$(docker image inspect -f '{{.Config.WorkingDir}}' $base_image)"
    workdir_base_image=`sed -e 's/^"//' -e 's/"$//' <<<"$workdir_base_image"`
    encrypted_files_string=''
    for i in "${ef_files_list[@]}"
    do
        if [[ "$i" =~ ^/.* ]]; then
            encrypted_files_string+='\n  { path = "'$i'", uri = "file:'$i'", type = "encrypted" },'
        else
            encrypted_files_string+='\n  { path = "'$workdir_base_image'/'$i'", uri = "file:'$i'", type = "encrypted" },'
        fi
    done

    if ! grep -q '^fs.mounts[[:space:]]*=[[:space:]]*\[' $app_image_manifest; then
        encrypted_files_string="fs.mounts = [$encrypted_files_string\n]"
        echo -e $encrypted_files_string >> $app_image_manifest
    else
        sed -i 's|\(^fs.mounts[[:space:]]*=[[:space:]]*\[\)|\1'"$encrypted_files_string"'|' $app_image_manifest
    fi
}

add_encryption_key_to_manifest() {
    if [[ ! -e $1 ]]; then
        echo "Encryption key was not found!"
        exit
    fi
    echo -e 'fs.insecure__keys.default = "'$(xxd -p $1)'"' >> $app_image_manifest
}

process_encrypted_files() {
    input_file="../$workload_type/base_image_helper/encrypted_files.txt"
    if [[ ! -e $input_file || -z "$(<$input_file)" ]]; then
        return
    fi

    add_encrypted_files_to_manifest $(<$input_file)
    encryption_key="../$workload_type/base_image_helper/encryption_key"
    add_encryption_key_to_manifest $encryption_key
}

cmdline_flag=""
create_gsc_image () {
    echo
    cd $CUR_DIR
    rm -rf gsc >/dev/null 2>&1
    git clone --depth 1 --branch v1.5 https://github.com/gramineproject/gsc.git
    cd gsc
    cp -f config.yaml.template config.yaml
    sed -i 's|ubuntu:.*|'$distro'"|' config.yaml

    ./gsc build $cmdline_flag --buildtype $1 $app_image_x  $WORKLOAD_DIR/$app_image_manifest

    echo
    docker tag gsc-$app_image_x-unsigned gsc-$base_image-unsigned
    password_arg=''
    if [[ "$signing_input" != "test" && "$2" != "" ]]; then
        password_arg="-p $2"
    fi
    ./gsc sign-image $base_image $signing_key_path $password_arg
    docker rmi -f gsc-$base_image-unsigned gsc-$app_image_x-unsigned $app_image_x >/dev/null 2>&1

    ./gsc info-image gsc-$base_image

    cd ../
    rm -rf $CUR_DIR'/test' >/dev/null 2>&1
}

# Signing key
echo ""
read -r signing_input signing_key_path <<<$(echo "$4 $4")
if [ "$signing_input" = "test" ]; then
    cmdline_flag="--insecure-args"
    echo 'Generating signing key'
    openssl genrsa -3 -out $CUR_DIR'/test/enclave-key.pem' 3072
    signing_key_path=$CUR_DIR'/test/enclave-key.pem'
    grep -qxF 'sgx.file_check_policy = "allow_all_but_log"' $app_image_manifest ||
     echo 'sgx.file_check_policy = "allow_all_but_log"' >> $app_image_manifest
fi

# CMD instruction for Dockerfile having all the command-line arguments
if [[ $5 ]]; then
    echo "$5" >> $wrapper_dockerfile
fi

# Test image creation
if [ "$6" = "test-image" ]; then
    cmdline_flag="--insecure-args"
    grep -qxF 'sgx.file_check_policy = "allow_all_but_log"' $app_image_manifest ||
     echo 'sgx.file_check_policy = "allow_all_but_log"' >> $app_image_manifest

    process_encrypted_files
    create_base_wrapper_image
    create_gsc_image $7
    exit 1
fi

# Get Attestation Input
attestation_required=$6
if [ "$attestation_required" = "y" ]; then
    ca_cert_path=$8
    cp -f $CUR_DIR/$ca_cert_path ca.crt
    copy_cert_files='COPY ca.crt /'
    echo '' >> $app_image_manifest
    echo '# Attestation related entries' >> $app_image_manifest
    echo 'sgx.remote_attestation = "dcap"' >> $app_image_manifest

    # Preload `libsecret_prov_attest.so` library. But if `LD_PRELOAD` exists in workload
    # specific manifest, then we must concatenate our lib with already-listed libs.
    secret_prov_attest="/gramine/meson_build_output/lib/x86_64-linux-gnu/libsecret_prov_attest.so"
    if ! grep -q 'loader.env.LD_PRELOAD' $app_image_manifest; then
        echo 'loader.env.LD_PRELOAD = "'$secret_prov_attest'"' >> $app_image_manifest
    else
        sed -i "s|\(^loader.env.LD_PRELOAD[[:space:]]*=[[:space:]]*.*\)\"|\1:$secret_prov_attest\"|g" \
            $app_image_manifest
    fi

    echo 'loader.env.SECRET_PROVISION_SERVERS = { passthrough = true }' >> $app_image_manifest
    echo 'loader.env.SECRET_PROVISION_CONSTRUCTOR = "1"' >> $app_image_manifest
    echo 'loader.env.SECRET_PROVISION_CA_CHAIN_PATH = "/ca.crt"' >> $app_image_manifest
    echo '# loader.env.SECRET_PROVISION_SET_KEY = "default"' >> $app_image_manifest
    echo '' >> $app_image_manifest
fi

# Environment Variables:
env_required=$9
if [ "$env_required" = "y" ]; then
    envs=${10}
    echo '' >> $app_image_manifest
    echo '# User Provided Environment Variables' >> $app_image_manifest

    re_pattern='-e[[:space:]]*([^[:space:].=]*="[^"]*")'
    while [[ $envs =~ $re_pattern ]]; do
        echo "loader.env.${BASH_REMATCH[1]}" >> $app_image_manifest
        envs=${envs#*${BASH_REMATCH[1]}}
    done
    echo ""
fi

# Encrypted Files Section
encrypted_files_required=${11}
if [ "$encrypted_files_required" = "y" ]; then
    ef_files=${12}
    add_encrypted_files_to_manifest ${12}

    if [ "$attestation_required" = "y" ]; then
        sed -i 's|.*SECRET_PROVISION_SET_KEY.*|loader.env.SECRET_PROVISION_SET_KEY = "default"|' \
            $app_image_manifest
    else
        add_encryption_key_to_manifest ${13}
    fi
fi

echo ""
create_base_wrapper_image
if [ "$attestation_required" = "y" ]; then
    rm ca.crt
fi
create_gsc_image $7 ${14}
