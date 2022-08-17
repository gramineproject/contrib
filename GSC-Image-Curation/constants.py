#!/usr/bin/env python

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

title = "Curate  Your  Own  Gramine  Sheilded  Container (GSC) Image !!!"

user_win_title = 'User Agent'
help_win_title = 'Commentary'

introduction = ['This application will provide step-by-step guidance in creating your own custom '
                'containers protected by Gramine. The commentary window to the right will provide'
                ' more context for each of the steps.', 'Do not resize this terminal window, Press'
                ' CTRL+G to get started!']

index = ['The target deployment environment is assumed to be an Azure Confidential compute instance'
         ' with out of tree DCAP driver. Following stages are involved in the GSC image curation:',
         'Enclave Signing Key', 'Attestation', 'Secret Provisioning', 'Encrypted Files',
         'Environment Variables', 'Runtime Arguments', 'Execution & Debug']

key_prompt = ['>> Enclave signing key:' , 'Please provide path to your signing key in the blue box:'
              ' (press CTRL+G when done; no input will autogenerate a test key)']
signing_key_help = ['SGX requires RSA 3072 keys with public exponent equal to 3. You can generate '
                    'signing key for learning and testing purposes using this command:',
                    'openssl genrsa -3 -out enclave-key.pem 3072' + color_set]

attestation_prompt = ['Do you require remote attestation? Enter y or CTRL+G to skip.']
attestation_help = ['https://gramine.readthedocs.io/en/stable/attestation.html']

server_ca_cert_prompt = ['>> Remote Attestation:' , 'To enable remote attestation using Azure DCAP '
                         'client libs, use another terminal to copy the ca.crt, server.crt, and '
                         'server.key certificates to gsc_image_curation/verifier_image/ssl directory ',
                         "NOTE: Attestation is required for using Gramine's Encrypted Filesystem, "
                         'for example to provision a decryption key for encrypted files, after a '
                         'successful attestation','- Type done and press CTRL+G when ready, OR',
                         '- Type test and press CTRL+G to create test certificates',
                         '- OR press CTRL+G to skip attestation']
server_ca_help = ['This step enables the host enclave to communicate to a remote verifier over an '
                  'RA-TLS link. This remote verifier uses Azure DCAP client libs to verify the Quote '
                  'supplied by the host enclave. RA-TLS attestation flow requires you to provide a '
                  'set of certificates and keys to enable the attestation flow. The CA certificate '
                  'will be used to TLS authenticate the verifier during the Remote Attestation '
                  'TLS (RA_TLS) flow. A test sample set of RA-TLS keys and certs are provided here.',
                  'https://github.com/gramineproject/contrib/tree/master/Examples/aks-attestation/ssl',
                  'For further reading - ', 'https://gramine.readthedocs.io/en/stable/attestation.html']

encrypted_files_prompt = ['>> Encrypted File System:', 'If the base image contain encrypted data, '
                         'please provide the path to these files. Accepted format: file1:path_relative_path/file2:file3',
                         'E.g., for gsc_image_creation/pytorch/pytorch_with_encrypted_files/Dockerfile '
                         'based image, the encrypted files input would be --> ',
                         'classes.txt:input.jpg:alexnet-pretrained.pt:app/result.txt' + color_set]
encypted_files_help = ["Gramine's Encrypted FS feature supports transparently decrypting data using"
                       " the encryption key that will be provisioned after successful attestation."]

arg_input = ['>> Runtime Arguments:', 'Specify docker run-time arguments here in a single string. '
            'for eg, if your docker runtime is ', 'docker run -it bash -c ls' + color_set, 'then the '
            'arg that needs to be provided here is', '-c ls' + color_set]
arg_help = ['Allowing an attacker to control executable arguments can break the security of the '
            'resulting enclave. Gramine will ignore any arguments provided at docker run-time, '
            'so ensure those are provided here now']

env_input = ['>> Runtime Environments:', 'Please specify a list of env variables and respective '
             'values separated by comma', 'Accepted format:', 'name="Xyz",age="20"' + color_set]
env_help =  ['This step secures the environment variables. Gramine will ignore environment '
             'variables specified at runtime, so please ensure you provide those here.']
wait_message = ['Image Creation:', 'Your Gramine Shielded Container image is being created. '
                'This might take a few minutes.']
system_config_message = ['System config by default is assumed to be an Azure instance with kernel'
                         ' , with Out of band SGX DCAP driver. The defaults can be modified in the'
                         ' system_config file']
run_command_no_att = 'docker run --net=host --device=/dev/sgx/enclave -it {}'
run_with_debug = 'python curate.py -d {}/{}' + color_set
extra_debug_instr = "It's also possible that you may run into issues resulting from lack of " \
                    'sufficient enclave memory pages, or insufficient number of threads. ' \
                    'The {}.manifest can be modified to change the defaults.'
