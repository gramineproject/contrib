#!/bin/bash

# This script takes input from GSC-Image-Curation/curate.py and creates gsc image.
# The script can be called either for test image or for custom image.
#
# The test image is created when user runs `python ./curate.py workload/<user_image> test` command.
# test image will create a gsc image for the user_image with test enclave key, debug enclave
# and no attestation support.
#
# In case of test image, the script takes 6 input parameters, whereas in case of custom image 11
# parameter are passed through curate.py.
#
# GSC-Image-Curation/curate.py calls this script after taking all the user inputs. This script does
# not interact with user, it just processes the input received from curate.py and produces the final
# gsc image.


# The input parameters in sequence are below:
#   Argument                      Expected
#   number                         Value
# -- arg1    : base_image_type e.g., redis or pytorch
# -- arg2    : base_image_name e.g., <your_image_name>
# -- arg3    : gsc sign key path or 'test-key' (in case of no key)
# -- arg4    : runtime argument string
# -- arg5    : [test image case] 'test-image' (to create a test image)
# -- arg6    : [test image case] true (then builds gsc with -d option) or false
# -- arg5    : [custom image case] y or n (in case of attestation required)
# -- arg6    : [custom image case] verifier's ca certificate path
# -- arg7    : y or n (whether user has environment variables or not)
# -- arg8    : actual environment variable string
# -- arg9    : y or n (whether user has encrypted files as part of base image or not)
# -- arg10   : actual encrypted files string
# -- arg11   : true (then builds gsc with -d option) or false

echo printing args $0 $@
start=$1
wrapper_dockerfile=$start"-gsc.dockerfile"
app_image_manifest=$start".manifest"

cd $start
cp $wrapper_dockerfile".template" $wrapper_dockerfile
cp $app_image_manifest".template" $app_image_manifest

base_image="$2"
# Set base image name in the dockerfile
sed -i 's|From.*|From '$base_image'|' $wrapper_dockerfile

if [[ "$base_image" == *":"* ]]; then
    app_image_x=$(echo $base_image | sed "s/:/_x:/")
else
    app_image_x="${base_image}_x"
fi

create_base_wrapper_image () {
    docker rmi -f $app_image_x >/dev/null 2>&1
    docker build -f $wrapper_dockerfile -t $app_image_x .
}

create_gsc_image () {
    # Download gsc that has dcap already enabled
    echo ""
    rm -rf gsc >/dev/null 2>&1
    git clone https://github.com/gramineproject/gsc.git
    cp $signing_key_path gsc/enclave-key.pem

    # delete the signing key created by the script
    rm enclave-key.pem >/dev/null 2>&1

    cd gsc
    cp ../util/config.yaml config.yaml

    # Delete already existing gsc image for the base image
    docker rmi -f gsc-$base_image >/dev/null 2>&1
    docker rmi -f gsc-$base_image-unsigned >/dev/null 2>&1

    if [ "$1" = "true" ]; then
        ./gsc build -d $app_image_x  ../$start/$app_image_manifest
    else
        ./gsc build $app_image_x ../$start/$app_image_manifest
    fi

    echo ""
    echo ""

    docker tag gsc-$app_image_x-unsigned gsc-$base_image-unsigned
    docker rmi gsc-$app_image_x-unsigned
    if [ signing_key_path != 'no-sign' ]; then
        ./gsc sign-image $base_image enclave-key.pem
    fi

    cd ../
    rm -rf gsc >/dev/null 2>&1

    # cleaning up intermediate images
    docker rmi -f gsc-$app_image-unsigned >/dev/null 2>&1
    docker rmi -f $app_image >/dev/null 2>&1
}

fetch_base_image_config () {
    base_image_config="$(docker image inspect "$base_image" | jq '.[].Config.'$1'')"
    if [[ "$base_image_config" = "null" || "$base_image_config" = "Null" || "$base_image_config" = "NULL" ]]; then
        config_string=''
    else
        base_image_config=$(echo $base_image_config | sed 's/[][]//g')
        IFS=',' #setting comma as delimiter
        read -a base_image_config_list <<<"$base_image_config"
        config_string=' '
        for i in "${base_image_config_list[@]}"
        do
            i=$(echo $i | sed "s/\"//g")
            config_string+=$i' '
        done
    fi
    echo $config_string
}

# Signing key
echo ""
signing_key_path="$3"
if [ "$signing_key_path" = "test-key" ]; then
    echo "Generating signing key"

    # Exit $start directory as we want enclave key to be present in $gsc_image_creation directory
    cd ..
    openssl genrsa -3 -out enclave-key.pem 3072
    signing_key_path="enclave-key.pem"
    cd $start
    grep -qxF 'sgx.file_check_policy = "allow_all_but_log"' $app_image_manifest ||
     echo 'sgx.file_check_policy = "allow_all_but_log"' >> $app_image_manifest
fi

# Runtime arguments:
args=$4
if [[ "$start" = "redis" ]]; then
    args+=" --protected-mode no --save ''"
fi
# Forming a complete binary string
# (format: <Base image entrypoint> <Base image cmd> <user provided runtime args>)
entrypoint_string=$(fetch_base_image_config "Entrypoint")
cmd_string=$(fetch_base_image_config "Cmd")
complete_binary_cmd=$entrypoint_string''$cmd_string''$args

# Creating entrypoint script file
entrypoint_script=entry_script_$start.sh
rm -f $entrypoint_script >/dev/null 2>&1
touch $entrypoint_script

# Copying the complete binary string to the entrypoint script file
echo "#!/bin/bash" >> $entrypoint_script
echo "" >> $entrypoint_script
echo "$complete_binary_cmd" >> $entrypoint_script

# test image creation
if [ "$5" = "test-image" ]; then
    grep -qxF 'sgx.file_check_policy = "allow_all_but_log"' $app_image_manifest ||
     echo 'sgx.file_check_policy = "allow_all_but_log"' >> $app_image_manifest
    create_base_wrapper_image
    # Exit from $start directory
    cd ..
    create_gsc_image $6
    exit 1
fi

# Get Attestation Input
attestation_required=$5
if [ "$attestation_required" = "y" ]; then
    ca_cert_path=$6

    # Exiting $start directory as the path to the ca cert can be w.r.t to 
    # gsc_image_curation directory
    cd ../
    cp $ca_cert_path $start/ca.crt
    cd $start
    sed -i 's|.*ca.crt.*|COPY ca.crt /ca.crt|' $wrapper_dockerfile
    echo '' >> $app_image_manifest
    echo '# Attestation related entries' >> $app_image_manifest
    echo 'sgx.remote_attestation = "dcap"' >> $app_image_manifest
    echo 'loader.env.LD_PRELOAD = "/gramine/meson_build_output/lib/x86_64-linux-gnu/libsecret_prov_attest.so"' >> $app_image_manifest
    echo 'loader.env.SECRET_PROVISION_SERVERS = { passthrough = true }' >> $app_image_manifest
    echo 'loader.env.SECRET_PROVISION_CONSTRUCTOR = "1"' >> $app_image_manifest
    echo 'loader.env.SECRET_PROVISION_CA_CHAIN_PATH = "/ca.crt"' >> $app_image_manifest
    echo '# loader.env.SECRET_PROVISION_SET_KEY = "default"' >> $app_image_manifest
    echo '' >> $app_image_manifest
    allowed_files=$'sgx.allowed_files = [\n"file:/etc/resolv.conf",\n]'
    echo "$allowed_files">> $app_image_manifest
fi

# Environment Variables:
env_required=$7
if [ "$env_required" = "y" ]; then
    envs=$8
    IFS=',' #setting comma as delimiter
    read -a env_list <<<"$envs" #reading str as an array as tokens separated by IFS
    echo '' >> $app_image_manifest
    echo '# User Provided Environment Variables' >> $app_image_manifest
    for i in "${env_list[@]}"
    do
        env_string='loader.env.'
        env_string+=$i
    echo "$env_string" >> $app_image_manifest
    done
    echo ""
fi

# Encrypted Files Section
encrypted_files_required=$9
if [ "$encrypted_files_required" = "y" ]; then
    ef_files=${10}
    IFS=':' #setting colon as delimiter
    read -a ef_files_list <<<"$ef_files"
    unset IFS
    echo '' >> $app_image_manifest
    echo '# User Provided Encrypted files' >> $app_image_manifest
    echo 'fs.mounts = [' >> $app_image_manifest
    workdir_base_image="$(docker image inspect "$base_image" | jq '.[].Config.WorkingDir')"
    workdir_base_image=`sed -e 's/^"//' -e 's/"$//' <<<"$workdir_base_image"`
    for i in "${ef_files_list[@]}"
    do
        encrypted_files_string=''
        encrypted_files_string+='  { path = "'$workdir_base_image'/'
        encrypted_files_string+=$i'", '
        encrypted_files_string+='uri = "file:'
        encrypted_files_string+=$i'", '
        encrypted_files_string+='type = "encrypted" },'
        echo "$encrypted_files_string" >> $app_image_manifest
    done
    echo "]" >> $app_image_manifest
    sed -i 's|.*SECRET_PROVISION_SET_KEY.*|loader.env.SECRET_PROVISION_SET_KEY = "default"|' $app_image_manifest
fi

# Generating wrapper for base image
create_base_wrapper_image
echo ""
if [ "$attestation_required" = "y" ]; then
    rm ca.crt
fi

if [[ "${11}" = "true" && "$signing_key_path" != "test-key" && "$start" = "redis" ]]; then
    echo 'loader.pal_internal_mem_size = "192M"' >> $app_image_manifest
fi

# Exit from $start directory
cd ..
create_gsc_image ${11}
