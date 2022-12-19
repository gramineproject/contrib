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
# -- arg5    : string with command-line arguments (hard-coded in Docker image via Gramine manifest)
# -- arg6    : 'test-image' string to create a non-production GSC image when curate.py is run in
#            :  test mode
#            : y or n (attestation required?) in case of custom image creation
# -- arg7    : y or n (build GSC with debug?)
# -- arg8    : verifier's ca certificate path
# -- arg9    : y or n (environment variables available?)
# -- arg10   : Actual environment variable string
# -- arg11   : y or n (encrypted files as part of base image?)
# -- arg12   : Path to the encrypted files in the image
# -- arg13   : Passphrase to the enclave signing key (if applicable)

echo printing args $0 $@

start=$1
wrapper_dockerfile=$start'-gsc.dockerfile'
app_image_manifest=$start'.manifest'

CUR_DIR=$(pwd)
WORKLOAD_DIR=$CUR_DIR'/workloads/'$start
cd $WORKLOAD_DIR
mkdir $CUR_DIR'/test' >/dev/null 2>&1

cp $wrapper_dockerfile'.template' $wrapper_dockerfile
cp $app_image_manifest'.template' $app_image_manifest

base_image="$2"
distro="$3"
# Set base image name in the dockerfile
sed -i 's|^FROM <base_image_name>$|FROM '$base_image'|' $wrapper_dockerfile

if [[ "$base_image" == *":"* ]]; then
    app_image_x=$(echo $base_image | sed "s/:/_x:/")
else
    app_image_x="${base_image}_x"
fi

create_base_wrapper_image () {
    docker rmi -f $app_image_x >/dev/null 2>&1
    docker build -f $wrapper_dockerfile -t $app_image_x .
}

add_encrypted_files_to_manifest(){
    IFS=':' # Setting colon as delimiter
    read -a ef_files_list <<<"$1"
    unset IFS
    echo '' >> $app_image_manifest
    echo '# User Provided Encrypted files' >> $app_image_manifest
    echo 'fs.mounts = [' >> $app_image_manifest
    workdir_base_image="$(docker image inspect "$base_image" | jq '.[].Config.WorkingDir')"
    workdir_base_image=`sed -e 's/^"//' -e 's/"$//' <<<"$workdir_base_image"`
    for i in "${ef_files_list[@]}"
    do
        encrypted_files_string='  { path = "'$workdir_base_image'/'$i'", uri = "file:'$i'", '
        encrypted_files_string+='type = "encrypted" },'
        echo "$encrypted_files_string" >> $app_image_manifest
    done
    echo "]" >> $app_image_manifest
}

cmdline_flag=""
create_gsc_image () {
    echo
    cd $CUR_DIR
    rm -rf gsc >/dev/null 2>&1
    git clone --depth 1 --branch v1.3.1 https://github.com/gramineproject/gsc.git
    cp $signing_key_path gsc/enclave-key.pem

    cd gsc
    cp ../util/config.yaml.template config.yaml
    sed -i 's|ubuntu:.*|'$distro'"|' config.yaml

    # Delete already existing GSC image for the base image
    docker rmi -f gsc-$base_image >/dev/null 2>&1
    docker rmi -f gsc-$base_image-unsigned >/dev/null 2>&1

    if [ "$1" = "y" ]; then
        ./gsc build $cmdline_flag -d $app_image_x  $WORKLOAD_DIR/$app_image_manifest
    else
        ./gsc build $cmdline_flag $app_image_x $WORKLOAD_DIR/$app_image_manifest
    fi

    echo
    docker tag gsc-$app_image_x-unsigned gsc-$base_image-unsigned
    password_arg=''
    if [[ "$signing_input" != "test" && "$2" != "" ]]; then
        password_arg="-p $2"
    fi
    ./gsc sign-image $base_image enclave-key.pem $password_arg
    docker rmi -f gsc-$base_image-unsigned >/dev/null 2>&1
    docker rmi gsc-$app_image_x-unsigned
    docker rmi -f $app_image_x >/dev/null 2>&1
    ./gsc info-image gsc-$base_image

    cd ../
    rm -rf gsc >/dev/null 2>&1
    rm -rf $CUR_DIR'/test' >/dev/null 2>&1
}

fetch_base_image_config () {
    base_image_config="$(docker image inspect "$base_image" | jq '.[].Config.'$1'')"
    if [[ "$base_image_config" = "null" || "$base_image_config" = "Null" ||
          "$base_image_config" = "NULL" ]]; then
        config_string=''
    else
        base_image_config=$(echo $base_image_config | sed 's/[][]//g')
        config_string=$(echo $base_image_config | sed 's/"\s*,\s*"/" "/g')
    fi
    echo $config_string
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

# Command-line arguments:
args=$5
if [[ "$start" = "redis" ]]; then
    args+=" --protected-mode no --save ''"
fi

# Forming a complete binary string
entrypoint_string=$(fetch_base_image_config "Entrypoint")
cmd_string=$(fetch_base_image_config "Cmd")
complete_binary_cmd="$entrypoint_string "

if [[ "$args" = "" ]]; then
    complete_binary_cmd+=$cmd_string
else
    complete_binary_cmd+=$args
fi

# Creating entrypoint script file
entrypoint_script=entry_script_$start.sh
rm -f $entrypoint_script >/dev/null 2>&1
touch $entrypoint_script

# Copying the complete binary string to the entrypoint script file
echo '#!/bin/bash' >> $entrypoint_script
echo '' >> $entrypoint_script

# TODO: This is a workaround, actual fix will go in GSC with PR #113
# This workaround should be removed when contrib starts using GSC v1.4 with PR #113 merged
echo 'if [[ "$#" -le "1" && "$1" -eq "" ]]; then
    '$complete_binary_cmd'
else
    '$complete_binary_cmd ' "${@}"
fi' >> $entrypoint_script

# Test image creation
if [ "$6" = "test-image" ]; then
    cmdline_flag="--insecure-args"
    grep -qxF 'sgx.file_check_policy = "allow_all_but_log"' $app_image_manifest ||
     echo 'sgx.file_check_policy = "allow_all_but_log"' >> $app_image_manifest

    if [[ "$start" = "pytorch" ]]; then
        encrypted_files='classes.txt:input.jpg:alexnet-pretrained.pt:result.txt'
        add_encrypted_files_to_manifest $encrypted_files
        var=$(xxd -p ../pytorch/base_image_helper/encryption_key)
        echo 'fs.insecure__keys.default = "'$var'"' >> $app_image_manifest
    fi

    create_base_wrapper_image
    create_gsc_image $7
    exit 1
fi

# Get Attestation Input
attestation_required=$6
if [ "$attestation_required" = "y" ]; then
    ca_cert_path=$8
    cp $CUR_DIR/$ca_cert_path ca.crt
    sed -i 's|.*ca.crt.*|COPY ca.crt /ca.crt|' $wrapper_dockerfile
    echo '' >> $app_image_manifest
    echo '# Attestation related entries' >> $app_image_manifest
    echo 'sgx.remote_attestation = "dcap"' >> $app_image_manifest
    echo 'loader.env.LD_PRELOAD = ' \
    '"/gramine/meson_build_output/lib/x86_64-linux-gnu/libsecret_prov_attest.so"' >> \
    $app_image_manifest
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
    sed -i 's|.*SECRET_PROVISION_SET_KEY.*|loader.env.SECRET_PROVISION_SET_KEY = "default"|' \
    $app_image_manifest
fi

echo ""
if [[ "$7" = "y" && "$signing_input" != "test" && "$start" = "redis" ]]; then
    echo 'loader.pal_internal_mem_size = "192M"' >> $app_image_manifest
fi

create_base_wrapper_image
if [ "$attestation_required" = "y" ]; then
    rm ca.crt
fi
create_gsc_image $7 ${13}
