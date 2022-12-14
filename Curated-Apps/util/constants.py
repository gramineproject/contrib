#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

title_height = 3
screen_height = 35
screen_width = 120
user_input_height = 5
user_input_width = screen_width
user_input_start_y = screen_height - user_input_height
num_sub_titles = 2
title_width = screen_width
sub_title_width = title_width / num_sub_titles
user_console_height = guide_win_height = screen_height - user_input_height - title_height
user_console_width = int(screen_width/2) - 3
guide_win_height = screen_height - user_input_height - title_height
guide_win_width = int(screen_width/2) - 2
line_offset = 2
partition_height = 20
partition_width = 1
partition_y = 7

color_set = '::reverse'

test_image_mssg = ('Your test GSC image is being generated. This image is not supposed to be'
                   ' used in production \n\n')

test_run_instr = ('Run the {} docker image in an Azure Confidential Compute'
                  ' instance using the below command.\n\n'
                  'Host networking (--net=host) is optional\n\n{}\n\n'
                  'Above command is saved to command.txt as well.'
                  ' Press any key to exit the app')
test_run_cmd = ('$ docker run --net=host --device=/dev/sgx/enclave:/dev/sgx_enclave -it {}')
image_not_found_warn = ('Warning: Cannot find application Docker image `{}`.\n'
                        'Fetching from Docker Hub ...\n\n')
log_progress = 'You may monitor {} for detailed progress\n\n'
title = "Curate a Gramine Shielded Container (GSC) image"

user_win_title = 'User Agent'
help_win_title = 'Commentary'

introduction = ['This application will provide step-by-step guidance for creating your own custom'
                ' containers protected by Gramine. The commentary window to the right will provide'
                ' more context for each of the steps.', 'Do not resize this terminal window.',
                'Press CTRL+G to get started!']

index = ['The target deployment environment is assumed to be an Azure Confidential compute'
         ' instance.','Following stages are involved in the GSC image curation:',
         '1. Distro selection',
         '2. Command-line arguments',
         '3. Environment variables',
         '4. Additional docker run flags',
         '5. Encrypted files and key provisioning',
         '6. Remote Attestation',
         '7. Enclave signing',
         '8. Generation of the final curated images',
         '9. Generation of docker run commands']

distro_prompt = ['>> Distro Selection:', 'Provide the distro of your base image',
                 '- Press 1 for Ubuntu 18.04',
                 '- Press 2 for Ubuntu 20.04',
                 '- Press 3 for Debian 10',
                 '- Press 4 for Debian 11',
                 'Any other option or no input will default to Ubuntu 18.04.',
                 'Press CTRL+G when done.']
distro_help = ['Tested distros are Ubuntu 18.04 and Ubuntu 20.04']
key_prompt = ['>> Enclave signing:' ,
              '- Please provide path to your enclave signing key in the blue box, OR',
              '- Type test to generate a test signing key',
              'Press CTRL+G when done']
signing_key_help = ['SGX requires RSA 3072 keys with public exponent equal to 3. You can generate'
                    ' a signing key protected by a test passphrase using below command:',
                    'openssl genrsa -3 -aes128 -passout pass:test@123 -out enclave-key.pem 3072'
                    + color_set]
verifier_build_messg = 'Building the RA-TLS Verifier image, this might take couple of minutes'
verifier_log_help = 'You may monitor verifier/{} for progress'
attestation_prompt = ['>> Remote Attestation:' , 'To enable remote attestation using Azure DCAP'
                      ' client libs, use another terminal to copy the ca.crt, server.crt, and'
                      ' server.key certificates to Curated-Apps/verifier/ssl directory',
                      'NOTE: Encrypted Filesystem of Gramine requires Attestation to provision'
                      ' a decryption key for encrypted files.',
                      '- Type done when ready, OR',
                      '- Type test to create test certificates, OR',
                      '- No input (blank) to skip attestation',
                      'Press CTRL+G when done']
attestation_help = ['This step enables the enclave to communicate to a remote verifier over'
                    ' an Remote Attestation TLS (RA-TLS) link. This remote verifier uses Azure'
                    ' DCAP client libs to verify the Quote supplied by the enclave. RA-TLS'
                    ' attestation flow requires you to provide a set of certificates and keys to'
                    ' enable the attestation flow. The CA certificate will be used to TLS'
                    ' authenticate the verifier during the RA-TLS flow. A test sample set of'
                    ' RA-TLS keys and certs are provided here:',
                    'https://github.com/gramineproject/contrib/tree/master/Examples/aks-attestation/ssl',
                    'For further reading - ',
                    'https://gramine.readthedocs.io/en/stable/attestation.html']

encrypted_files_prompt = ['>> Encrypted files and key provisioning:', 'Please provide path of'
                          ' these files relative to the working directory:', '1. Encrypted files'
                          ' in the base image used by the application, if any.', '2. Files created'
                          ' at runtime, if any.', 'Accepted format: `file_path1:file_path2`',
                          'e.g. for workloads/pytorch/base_image_helper/Dockerfile based image,'
                          ' the encrypted files input would be --> ',
                          'classes.txt:input.jpg:alexnet-pretrained.pt:result.txt' + color_set,
                          'Press CTRL+G when done']
encypted_files_help = ["Gramine's Encrypted FS feature supports transparently decrypting data"
                       ' using the encryption key that will be provisioned after successful'
                       ' attestation.']
encryption_key_prompt = ('Please provide the path to the key used for the encryption. Press CTRL+G'
                         ' when done')
arg_input = ['>> Command-line arguments:', 'Specify docker command-line arguments here in a single'
             ' string. For example, if your docker runtime is ', 'docker run <image_name> arg1'
             ' arg2' + color_set, 'then the arguments that need to be provided here are', 'arg1'
             ' arg2' + color_set, 'Press CTRL+G when done']
arg_help = ['Allowing an attacker to control executable arguments can break the security of the'
            ' resulting enclave. Gramine will ignore any arguments provided at docker run-time,'
            ' so ensure those are provided here now']

env_input = ['>> Environment variables:', 'Please specify a list of env variables and respective'
             ' values in below mentioned format:',
             '-e ENV_NAME1="value1" -e ENV_NAME2="value2"' + color_set,
             'Press CTRL+G when done']
env_help =  ['This step secures the environment variables. Gramine will ignore environment'
             ' variables specified at runtime, so please ensure you provide those here.'
             ' By default Gramine will add all the environment variables set in the base'
             ' docker image.']

flags_input = ['>> Additional docker run flags:','Specify docker run flags here in a single string.'
             ' For example, if your docker command is ', 'docker run flag1 flag2 <image_name>'
             + color_set, 'then the flags that need to be provided here are', 'flag1 flag2'
             + color_set, 'Press CTRL+G when done']
flags_help =  ['At the end of this Curation app, it writes instructions into commands.txt to run'
               ' the curated images. If you have Docker container flags/configurations which should'
               ' be added to the `docker run` instructions, please specify them here or modify'
               ' the final commands in commands.txt at the end of curation.', 'Examples of'
               ' docker flags: --rm, --name, --network, etc.' + color_set]

wait_message = ['Image Creation:', 'Your Gramine Shielded Container image is being created.'
                ' This might take a few minutes.']
system_config_message = ['System config by default is assumed to be an Azure Confidential compute'
                         ' instance.']
run_command_no_att = '$ docker run {} --device=/dev/sgx/enclave:/dev/sgx_enclave -it {}'
run_with_debug = 'python3 curate.py {} {} debug' + color_set
extra_debug_instr = ("It's also possible that you may run into issues resulting from lack of"
                     ' sufficient enclave memory pages, or insufficient number of threads.'
                     ' The {}.manifest can be modified to change the defaults.')
app_exit_messg = 'Press CTRL+G to exit the application'
debug_run_messg = ('In the event of failures during runtime, run with debug flag (if not already)'
                   ' to get more information, as shown below:')
commands_file = 'commands.txt'
image_ready_messg  = ('The curated GSC image {} is ready, please follow the instructions in the'
                      ' below file to run your image(s).')
image_ready_messg_att = ('The curated GSC image , and the remote attestation verifier'
                         ' image is ready, You can run the images using the instructions provided'
                         ' in the below file.')
workload_run = ('$ docker run {} --device=/dev/sgx/enclave:/dev/sgx_enclave -e SECRET_PROVISION_SERVERS={}'
                ' -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -it {}')
enc_keys_mount = '-v {}:/keys'
enc_key_path = '/keys/{}'
ssl_folder_path_on_host = 'verifier/ssl_common'
verifier_cert_mount = '-v {}:/ra-tls-secret-prov/ssl'
debug_enclave_env_verifier = (' -e RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 -e'
                              ' RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1 ')
azure_warning = ['Warning: You are building'
                 ' these images on a non Azure Confidential Compute instance' + color_set,
                 'Please ensure you run the final images on an Azure VM or in the AKS cluster only'
                 ,'Press CTRL+G to continue']
azure_help = ['The target deployment environment is assumed to be an Azure Confidential compute'
              ' instance.']
verifier_log_file = 'verifier.log'
file_not_found_error = 'Error: {} file does not exist.'
CTRL_G = 7
