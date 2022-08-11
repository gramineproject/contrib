#!/usr/bin/env python
# encoding: utf-8
"""
constants.py
"""


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
guide_win_width = int(screen_width/2) - 3
line_offset = 2
partition_height = 20
partition_width = 1
partition_y = 7

title = "Curate  Your  Own  GSC  Image !!!"

user_win_title = 'User Agent (Start here)'

introduction = ['This application will guide you step by step in creating your own custom containers \
protected by Gramine. The commentary window to the right will provide more context for each of \
the steps.', 'Do not resize this terminal window, Press CTRL+G to get started!']

index = ['Signing', 'Attestation', 'Secret Provisioning', 'Encrypted Files', 'Environment Variables', 'Runtime Arguments', 'Execution']

key_prompt = ['>>> Please provide path to your signing key in the blue box: (press CTRL+G when done, no input will autogenerate a test key)']
signing_key_help = ["SGX requires RSA 3072 keys with public exponent equal to 3. You can generate signing" \
"key using this command: openssl genrsa -3 -out enclave-key.pem 3072"]

attestation_prompt = ['Do you require remote attestation? Enter y or CTRL+G to skip.']
attestation_help = ['https://gramine.readthedocs.io/en/stable/attestation.html']

server_ca_cert_prompt = ['Please open another terminal window and copy the ca.crt, server.crt,'
                'and server.key certificates to gsc_image_curation/verifier_image/ssl'
                ' directory. No input will result in the generation of test certificates that should be'
                'used only for learning purposes, and not in production.', 'Enter done when the above is done', 'Enter test to generate test certificates' , 'Enter CTRL+G to skip attestation']
server_ca_help = ['RA-TLS attestation flow requires you to provide a set of certificates and keys to enable the attestation flow.'
'This CA certificate will be used to verify the server during the Remote Attestation TLS (RA_TLS) flow. A sample set is provided'
'here - https://github.com/gramineproject/contrib/tree/master/Examples/aks-attestation/ssl']

encrypted_files_prompt = ['If the base image contain encrypted data, please provide the path to these files. ' \
'Accepted format: file1:path_relative_path/file2:file3', 'E.g., for gsc_image_creation/pytorch/pytorch_with_encrypted_files/Dockerfile' \
                   ' based image, the encrypted files input would be --> ', 'classes.txt:input.jpg:alexnet-pretrained.pt:app/result.txt']
encypted_files_help = ["Gramine's Encrypted FS feature supports transparently decrypting data using the" \
" encryption key that will be provisioned after successful attestation."]

arg_input = ['Please specify run-time arguments here in a single string.']
arg_help = ['Gramine will ignore any arguments provider at docker run-time, so ensure those are provided here now']

env_input = ['Please specify a list of env variables and respective values separated by comma' \
                '(accepted format: name="Xyz",age="20") -> ']
env_help =  ['Gramine will ignore any env specified at runtime, so please ensure you provide those here.']

