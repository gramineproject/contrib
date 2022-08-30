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

test_image_mssg = 'Your test GSC image is being generated. This image is not supposed to be ' \
                  'used in production \n\n'
test_run_instr = 'Run the {} docker image in an Azure Confidential Compute ' \
                 'instance using the below command. Host networking (--net=host) is optional\n\n' \
                 'docker run --net=host --device=/dev/sgx/enclave -it {}.\n\n' \
                 'Press any key to exit the app'
image_not_found_warn = 'Warning: Cannot find application Docker image `{}`.\n' \
                       'Fetching from Docker Hub ...\n\n'
log_progress = 'You may monitor {} for detailed progress'
title = "Curate  Your  Own  Gramine  Sheilded  Container (GSC) Image !!!"

user_win_title = 'User Agent'
help_win_title = 'Commentary'

introduction = ['This application will provide step-by-step guidance in creating your own custom '
                'containers protected by Gramine. The commentary window to the right will provide'
                ' more context for each of the steps.', 'Do not resize this terminal window, Press'
                ' CTRL+G to get started!']

index = ['The target deployment environment is assumed to be an Azure Confidential compute instance'
         ' with out of tree DCAP driver. Following stages are involved in the GSC image curation:',
         'Enclave Signing Key', 'Attestation', 'Secret Provisioning', 'Runtime Arguments',
         'Environment Variables', 'Encrypted Files', 'Execution & Debug']

key_prompt = ['>> Enclave signing key:' , '- Please provide path to your enclave signing key in the '
              'blue box, and press CTRL+G OR',
              "- Press n and CTRL+G if you don't want to sign the graminized image OR",
              '- Press CTRL+G without any input to generate a test signing key']
signing_key_help = ['SGX requires RSA 3072 keys with public exponent equal to 3. You can generate '
                    'signing key for learning and testing purposes using this command:',
                    'openssl genrsa -3 -out enclave-key.pem 3072' + color_set,
                    'You can also generate unsigned images incase you wish to sign them separately']
verifier_build_messg = 'Building the RA-TLS Verifier image, this might take couple of minutes'
verifier_log_help = 'You may monitor verifier/{} for progress'
attestation_prompt = ['>> Remote Attestation:' , 'To enable remote attestation using Azure DCAP '
                         'client libs, use another terminal to copy the ca.crt, server.crt, and '
                         'server.key certificates to gsc_image_curation/verifier/ssl directory ',
                         "NOTE: Attestation is required for using Gramine's Encrypted Filesystem, "
                         'for example to provision a decryption key for encrypted files, after a '
                         'successful attestation','- Type done and press CTRL+G when ready, OR',
                         '- Type test and press CTRL+G to create test certificates',
                         '- OR press CTRL+G to skip attestation']
attestation_help = ['This step enables the host enclave to communicate to a remote verifier over an '
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
                         'classes.txt:input.jpg:alexnet-pretrained.pt:result.txt' + color_set,
                         'Press CTRL+G when done']
encypted_files_help = ["Gramine's Encrypted FS feature supports transparently decrypting data using"
                       " the encryption key that will be provisioned after successful attestation."]
encryption_key_prompt = 'Please provide the path to the key used for the encryption.'
arg_input = ['>> Runtime Arguments:', 'Specify docker run-time arguments here in a single string. '
            'for eg, if your docker runtime is ', 'docker run -it bash -c ls' + color_set, 'then the '
            'arg that needs to be provided here is', '-c ls' + color_set, 'Press CTRL+G when done']
arg_help = ['Allowing an attacker to control executable arguments can break the security of the '
            'resulting enclave. Gramine will ignore any arguments provided at docker run-time, '
            'so ensure those are provided here now']

env_input = ['>> Runtime Environments:', 'Please specify a list of env variables and respective '
             'values separated by comma', 'Accepted format:', 'name="Xyz",age="20"' + color_set,
             'Press CTRL+G when done']
env_help =  ['This step secures the environment variables. Gramine will ignore environment '
             'variables specified at runtime, so please ensure you provide those here.']
wait_message = ['Image Creation:', 'Your Gramine Shielded Container image is being created. '
                'This might take a few minutes.']
system_config_message = ['System config by default is assumed to be an Azure instance with kernel'
                         ' , with Out of band SGX DCAP driver. The defaults can be modified in the'
                         ' system_config file']
run_command_no_att = 'docker run {} --device=/dev/sgx/enclave -it {}'
run_with_debug = 'python curate.py -d {}/{}' + color_set
extra_debug_instr = "It's also possible that you may run into issues resulting from lack of " \
                    'sufficient enclave memory pages, or insufficient number of threads. ' \
                    'The {}.manifest can be modified to change the defaults.'
app_exit_messg = 'Press CTRL+G to exit the application'
sign_instr = 'Please follow the below instructions to sign the gsc image with your ' \
             'signing key:-\n' \
             'git clone https://github.com/gramineproject/gsc.git\n' \
             'cd gsc\n' \
             './gsc sign-image {} <enclave-key.pem>\n\n' \
             'Run the image(s) as shown below:\n'
debug_run_messg = 'Run with debug (-d) enabled to get more information in the event of failures ' \
                  'during runtime:'
commands_file = 'commands.txt'
image_ready_messg  = 'The curated GSC image {} is ready, please follow the instructions in the '\
                     'below file to run your image(s).'
image_ready_messg_att =  'The curated GSC image , and the remote attestation verifier ' \
                         'image is ready, You can run the images using the instructions provided' \
                         'in the below file.'
workload_run = 'docker run --rm {} --device=/dev/sgx/enclave -e SECRET_PROVISION_SERVERS={} ' \
               '-v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -it {}'
enc_keys_mount = '-v {}:/keys'
enc_key_path = '/keys/{}'
ssl_folder_path_on_host = 'verifier/ssl_common'
verifier_cert_mount = '-v {}:/ra-tls-secret-prov/ssl'
debug_enclave_env_verifier = ' -e RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 -e ' \
                                     'RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1 '
azure_warning = ['Warning: You are building '
        'these images on a non Azure Confidential Compute instance' + color_set, 'Please ensure you run the '
        'final images on an Azure VM or in the AKS cluster only', 'Press CTRL+G to continue']
azure_help =  ['The target deployment environment is assumed to be an Azure Confidential compute instance'
            ' with out of tree DCAP driver']
verifier_log_file = 'verifier.log'
file_nf_error = 'Error: {} file does not exist. Please follow instructions above'
CTRL_G = 7
