#!/usr/bin/python
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

# This script will provide step-by-step guidance in creating your own custom Docker images
# protected by Gramine. User will be prompted for input at every stage, and once the script has all
# the details, it will call a separate curation script (util/curation_script.sh) that takes the
# user provided inputs to create the graminized Docker image using GSC. This script also calls into
# another script (verifier/helper.sh) to generate the verifier Docker image (for SGX remote
# attestation). The generated verifier Docker image must be started on a trusted remote
# system before the graminized Docker image is deployed at the target system, to verify the SGX
# attestation evidence (SGX quote) sent by the latter image.

import curses
import docker
import os
import os.path
import re
import subprocess
import sys
import textwrap
import time

from cProfile import label
from util.constants import *
from curses import KEY_BACKSPACE, wrapper
from curses.textpad import Textbox, rectangle
from glob import escape
from os import path
from sys import argv

# Following are the command line parameters accepted by this script:
usage = '''
|---------------------------------------------------------------------------------------------|
| Required?| Argument         | Description/Possible values                                   |
|----------|------------------|---------------------------------------------------------------|
|    Yes   | <workload type>  | Provide type of workload e.g. redis or pytorch                |
|    Yes   | <base image name>| Base image name to be graminized.                             |
| Optional | 'debug'          | To generate an insecure graminized image with debug symbols.  |
| Optional | 'test'           | To generate an insecure image with a test enclave signing key.|
|---------------------------------------------------------------------------------------------|
'''
# -------GUI curses interfaces--------------------------------------------------------------------
def initwindows():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    WHITE_AND_BLACK = curses.color_pair(1)
    WHITE_AND_BLUE = curses.color_pair(2)

    title_win = curses.newwin(title_height, title_width, 0, 0)
    user_console = curses.newwin(user_console_height, user_console_width, title_height, 0)
    guide_win = curses.newwin(guide_win_height, guide_win_width, title_height,
                              int(screen_width/2))
    partition_win = curses.newwin(partition_height, partition_width, partition_y,
                                  int(sub_title_width) - 2)

    title_win.addstr(0, 0, ' ' * title_width, WHITE_AND_BLUE)
    title_win.addstr(0, int((title_width/2) - (len(title)/2)), title,
                     WHITE_AND_BLUE | curses.A_BOLD)

    sub_win_title = user_win_title
    sub_title_ind = 1

    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width) - (sub_title_width / 2)
                                            - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title,
                     WHITE_AND_BLACK | curses.A_BOLD | curses.A_UNDERLINE)

    partition_win.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    partition_win.refresh()

    sub_win_title = help_win_title
    sub_title_ind = 2
    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width)
                                           - (sub_title_width / 2) - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title,
                     WHITE_AND_BLACK | curses.A_BOLD | curses.A_UNDERLINE)
    title_win.refresh()
    return(user_console, guide_win)

def resize_screen(screen_height, screen_width):
    subprocess.call(['echo','-e',f'\x1b[8;{screen_height};{screen_width}t'])
    time.sleep(0.35)

def print_correct_usage(win, arg):
    win.addstr(usage)
    win.addstr('Press any key to exit')
    win.getch()
    sys.exit(1)

def update_user_input(secure=False):
    editwin = curses.newwin(user_input_height, user_input_width, user_input_start_y, 0)
    editwin.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    box = Textbox(editwin)
    if secure:
        user_input = secure_box_edit(box)
    else:
        box.edit()
        editwin.refresh()
        user_input = box.gather().strip().replace('\n', '')
    editwin.erase()
    editwin.refresh()
    return user_input

def secure_box_edit(box):
    user_inp_arr = []
    while 1:
        ch = box.win.getch()
        if ch == CTRL_G:
            break
        if ch == KEY_BACKSPACE:
            if len(user_inp_arr) > 0:
                user_inp_arr.pop()
        else:
            user_inp_arr.append(chr(ch))
        if not ch:
            continue
        if not box.do_command(ch):
            break
        [y, x] = box.win.getyx()
        if x > 0:
            box.win.addstr(y, int(x - 1), '*')
        box.win.refresh()
    return ''.join(user_inp_arr)

def update_user_and_commentary_win(user_console, guide_win, user_text, help_text, offset):
    user_console.erase()
    guide_win.erase()
    user_console.addstr(offset, 0, textwrap.fill(user_text, user_console_width))
    guide_win.addstr(offset, 0, textwrap.fill(help_text, guide_win_width))

    user_console.refresh()
    guide_win.refresh()

def update_user_and_commentary_win_array(user_console, guide_win, user_text_arr, help_text_arr):
    user_console.erase()
    guide_win.erase()

    for user_text in user_text_arr:
        color = 0
        if user_text.find(color_set) >= 0:
            color = curses.color_pair(2) | curses.A_REVERSE
            user_text = user_text.replace(color_set , '')
        [y, x] = user_console.getyx()
        user_console.addstr(y + line_offset, 0, textwrap.fill(user_text, user_console_width),
                            color)
    for help_text in help_text_arr:
        color = 0
        if help_text.find(color_set) >= 0:
            color = curses.color_pair(2) | curses.A_REVERSE
            help_text = help_text.replace(color_set , '')
        [y, x] = guide_win.getyx()
        guide_win.addstr(y + line_offset, 0, textwrap.fill(help_text, guide_win_width), color)
    user_console.refresh()
    guide_win.refresh()

def update_user_error_win(user_console, error_text):
    [y, _] = user_console.getyx()
    user_console.addstr(y + 2, 0, textwrap.fill(error_text, user_console_width), curses.A_BOLD
                        | curses.color_pair(3))
    user_console.refresh()

def edit_user_win(user_console, error_text):
    [y, _] = user_console.getyx()
    user_console.addstr(y + line_offset, 0, textwrap.fill(error_text, user_console_width))
    user_console.refresh()

def update_run_win(text):
    editwin = curses.newwin(user_input_height, user_input_width, user_input_start_y, 0)
    editwin.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)

    start = 0
    for text_input in text:
        editwin.addstr(start, 0, textwrap.fill(text_input, user_input_width),
                       curses.color_pair(2) | curses.A_BOLD)
        start = start + 2

    editwin.refresh()

# --------docker image curation support interfaces------------------------------------------------
def get_docker_image(docker_socket, image_name):
    try:
        docker_image = docker_socket.images.get(image_name)
        return docker_image
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        return None

def check_image_creation_success(win, docker_socket, image_name, log_file):
    image = get_docker_image(docker_socket, image_name)
    if image is None:
        win.addstr(f'\n\n\n`{image_name}` creation failed, exiting....')
        win.addstr(f'For more info, look at the log file here: {log_file}')
        win.getch()
        sys.exit(1)

def pull_docker_image(win, docker_socket, image_name):
    try:
        docker_image = docker_socket.images.pull(image_name)
        return 0
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        win.addstr(f'Error: Could not fetch `{image_name}` image from DockerHub.\n')
        win.addstr('Please check if the image name is correct and try again.')
        win.refresh()
        return -1

def get_encryption_key_input(user_console, guide_win):
    file = update_user_input()
    while not path.isfile(file):
        user_console.erase()
        update_user_and_commentary_win_array(user_console, guide_win, encrypted_files_prompt,
                                             encypted_files_help)
        edit_user_win(user_console, encryption_key_prompt)
        update_user_error_win(user_console, file_not_found_error.format(file))
        file = update_user_input()
    return file

# User is expected to provide the path to a signing key or `test` as input.
# `test` as an input will result in generating a test signing key which is insecure for use in
# production!
def get_enclave_signing_input(user_console, guide_win):
    sign_file = update_user_input()
    while not path.isfile(sign_file) and sign_file != 'test':
        error = "Please provide a valid input"
        if sign_file != '':
            error = file_not_found_error.format(sign_file)
        user_console.erase()
        update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
        update_user_error_win(user_console, error)
        sign_file = update_user_input()
    return sign_file

def get_attestation_input(user_console, guide_win):
    attestation_input = update_user_input()
    while True:
        while (attestation_input not in ['test', 'done', '']):
            user_console.erase()
            update_user_and_commentary_win_array(user_console, guide_win, attestation_prompt,
                                                 attestation_help)
            update_user_error_win(user_console, 'Invalid option specified')
            attestation_input = update_user_input()
        if attestation_input == 'done':
            if (path.isfile('verifier/ssl/ca.crt') and
                path.isfile('verifier/ssl/server.crt') and
                path.isfile('verifier/ssl/server.key')):
                return attestation_input
            user_console.erase()
            update_user_and_commentary_win_array(user_console, guide_win, attestation_prompt,
                                                 attestation_help)
            update_user_error_win(user_console, 'One or more files does not exist at'
                                  ' verifier/ssl/ directory')
            attestation_input = update_user_input()
            continue
        return attestation_input

def is_azure_instance():
    service_cmd = "systemctl --type=service --state=running"
    service_output = subprocess.run(service_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, shell=True)
    re_pattern='wa.*?agent.service.*?Azure.*'
    rec_pattern = re.compile(re_pattern, re.VERBOSE)

    return len(rec_pattern.findall(service_output.stdout)) > 0

def get_insecure_args(workload_type):
    args = ''
    insecure_args_file = 'workloads/'+workload_type+'/insecure_args.txt'

    if os.path.exists(insecure_args_file):
        try:
            with open(insecure_args_file, 'r') as pfile:
                for line in pfile:
                    if not line.startswith('#'):
                        args = line
                        break
        except:
            raise IOError
    return args


def main(stdscr, argv):

    if len(argv) < 3:
        print_correct_usage(stdscr, argv[0])

    workload_type = argv[1]
    base_image_name = argv[2]
    debug_flag = 'n'
    test_flag = ''
    processed_args = 3
    while processed_args < len(argv):
        if argv[processed_args] == 'debug':
            debug_flag = 'y'
            processed_args += 1
        elif argv[processed_args] == 'test':
            test_flag = 'test'
            processed_args += 1
        else:
            print_correct_usage(stdscr, argv[0])

    stdscr.clear()
    resize_screen(screen_height, screen_width)
    stdscr = curses.initscr()

    docker_socket = docker.from_env()
    base_image = get_docker_image(docker_socket, base_image_name)
    if base_image is None:
        stdscr.addstr(image_not_found_warn.format(base_image_name))
        stdscr.refresh()
        if pull_docker_image(stdscr, docker_socket, base_image_name) == -1:
            stdscr.getch()
            return -1

    log_file_name, n = re.subn('[:/]', '_', base_image_name)
    log_file = f'workloads/{workload_type}/{log_file_name}.log'
    log_file_pointer = open(log_file, 'w')

    gsc_app_image ='gsc-{}'.format(base_image_name)
    gsc_app_image_unsigned ='gsc-{}-unsigned'.format(base_image_name)

    distro = 'ubuntu:18.04'
    # Generating test image
    if test_flag:
        stdscr.addstr(test_image_mssg)
        stdscr.addstr(log_progress.format(log_file))
        stdscr.refresh()
        subprocess.call(['util/curation_script.sh', workload_type, base_image_name, distro,
                         'test', '', 'test-image', debug_flag], stdout=log_file_pointer,
                         stderr=log_file_pointer)
        check_image_creation_success(stdscr, docker_socket, gsc_app_image, log_file)
        try:
            args = get_insecure_args(workload_type)
        except IOError:
            stdscr.addstr('Could not open file '+'workloads/'+workload_type+'/insecure_args.txt')
            stdscr.getch()
            return -1
        string_t = test_run_cmd.format(gsc_app_image + ' ' + args)
        stdscr.addstr(test_run_instr.format(gsc_app_image, string_t))

        commands_fp = open(commands_file, 'w')

        commands_fp.write(test_run_cmd.format(gsc_app_image + ' ' + args))
        commands_fp.close()

        stdscr.getch()
        return 0

    user_console, guide_win = initwindows()

    update_user_and_commentary_win_array(user_console, guide_win, introduction, index)
    update_user_input()

    if not is_azure_instance():
        update_user_and_commentary_win_array(user_console, guide_win, azure_warning, azure_help)
        update_user_input()

    # 1. Obtain distro version
    update_user_and_commentary_win_array(user_console, guide_win, distro_prompt, distro_help)
    distro_option = update_user_input()
    if distro_option == '2':
        distro = 'ubuntu:20.04'
    elif distro_option == '3' or distro_option == '4':
        distro = 'debian:11'

    # 2. Provide command-line arguments
    update_user_and_commentary_win_array(user_console, guide_win, arg_input, arg_help)
    args = update_user_input()

    # 3. Provide environment variables
    update_user_and_commentary_win_array(user_console, guide_win, env_input, env_help)
    env_required = 'n'
    envs = update_user_input()
    if envs:
        env_required = 'y'

    # 4. Provide encrypted files and key provisioning
    ef_required = 'n'
    encryption_key = ''
    enc_key_path_in_verifier = ''
    encrypted_files = ''
    update_user_and_commentary_win_array(user_console, guide_win, encrypted_files_prompt,
                                         encypted_files_help)
    encrypted_files = update_user_input()

    if encrypted_files:
        edit_user_win(user_console, encryption_key_prompt)
        encryption_key = get_encryption_key_input(user_console, guide_win)
        encryption_key_name = os.path.basename(encryption_key)
        enc_key_path_in_verifier = enc_key_path.format(encryption_key_name)
        ef_required = 'y'

    # 5. Remote Attestation with RA-TLS
    ca_cert_path = ''
    config = ''
    verifier_server = '<verifier-dns-name:port>'
    attestation_required = 'n'
    host_net = ''
    update_user_and_commentary_win_array(user_console, guide_win, attestation_prompt,
                                         attestation_help)
    while True:
        attestation_input = get_attestation_input(user_console, guide_win)
        if attestation_input == 'done':
            attestation_required = 'y'
            ca_cert_path = ssl_folder_path_on_host+'/ca.crt'

        elif attestation_input == 'test':
            ca_cert_path, verifier_server = ssl_folder_path_on_host+'/ca.crt', '"localhost:4433"'
            host_net, config = '--net=host', 'test'
            attestation_required = 'y'

        if ef_required == 'y' and attestation_required == 'n':
            user_console.erase()
            update_user_and_commentary_win_array(user_console, guide_win, attestation_prompt,
                                                 attestation_help)
            error = ('You require Remote Attestation to provision the key for encrypted files.')
            update_user_error_win(user_console, error)
            continue

        break

    # 6. Obtain enclave signing key
    update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
    key_path = get_enclave_signing_input(user_console, guide_win)
    passphrase = ''
    if key_path == 'test':
        config = 'test'
    else:
        user_console.erase()
        update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
        edit_user_win(user_console, '>> Please enter the passphrase for the signing key'
                      ' (no input will assume a passphrase-less key)'
                      '                   Press CTRL+G to continue')
        passphrase = update_user_input(secure=True)

    # 7. Generation of the final curated images
    if attestation_required == 'y':
        os.chdir('verifier')
        verifier_log_file_pointer = open(verifier_log_file, 'w')
        update_user_and_commentary_win_array(user_console, guide_win, [verifier_build_messg],
                                             [verifier_log_help.format(verifier_log_file)])
        subprocess.call(['./helper.sh', attestation_input, ef_required,
                         enc_key_path_in_verifier], stdout=verifier_log_file_pointer,
                         stderr=verifier_log_file_pointer)
        os.chdir('../')
        check_image_creation_success(user_console, docker_socket,'verifier:latest',
                                     'verifier/'+verifier_log_file)

    update_user_and_commentary_win_array(user_console, guide_win, wait_message,
                                         [log_progress.format(log_file)])
    subprocess.call(['util/curation_script.sh', workload_type, base_image_name, distro,
                     key_path, args, attestation_required, debug_flag, ca_cert_path, env_required,
                     envs, ef_required, encrypted_files, passphrase], stdout=log_file_pointer,
                     stderr=log_file_pointer)
    image = gsc_app_image
    check_image_creation_success(user_console, docker_socket, image, log_file)

    # 8. Generation of docker run commands
    commands_fp = open(commands_file, 'w')
    if attestation_required == 'y':
        debug_enclave_env_ver_ext = ''
        if config == 'test':
            debug_enclave_env_ver_ext = debug_enclave_env_verifier

        ssl_folder_abs_path_on_host = os.path.abspath(ssl_folder_path_on_host)
        verifier_cert_mount_str = verifier_cert_mount.format(ssl_folder_abs_path_on_host)
        enc_keys_mount_str, enc_keys_path_str = '' , ''
        if encryption_key:
            key_name_and_path = os.path.abspath(encryption_key).rsplit('/', 1)
            enc_keys_mount_str =  enc_keys_mount.format(key_name_and_path[0])

        mr_enclave = '<mr_enclave>'
        mr_signer = '<mr_signer>'
        isv_prod_id = '<isv_prod_id>'
        isv_svn = '<isv_svn>'

        with open(log_file, 'r') as pfile:
            lines = pfile.read()
        pattern_enclave = re.compile('mr_enclave = \"(.*)\"')
        pattern_signer = re.compile('mr_signer = \"(.*)\"')
        pattern_isv_prod_id = re.compile('isv_prod_id = (.*)')
        pattern_isv_svn = re.compile('isv_svn = (.*)')

        mr_enclave_list = pattern_enclave.findall(lines)
        mr_signer_list = pattern_signer.findall(lines)
        isv_prod_id_list = pattern_isv_prod_id.findall(lines)
        isv_svn_list = pattern_isv_svn.findall(lines)

        if len(mr_enclave_list) > 0: mr_enclave = mr_enclave_list[0]
        if len(mr_signer_list) > 0: mr_signer = mr_signer_list[0]
        if len(isv_prod_id_list) > 0: isv_prod_id = isv_prod_id_list[0]
        if len(isv_svn_list) > 0: isv_svn = isv_svn_list[0]

        verifier_run_command = (f'Execute below command to start verifier on a trusted system:\n'
                                f'$ docker run {host_net} --device=/dev/sgx/enclave '
                                f'-e RA_TLS_MRENCLAVE={mr_enclave} -e RA_TLS_MRSIGNER={mr_signer} '
                                f'-e RA_TLS_ISV_PROD_ID={isv_prod_id} -e RA_TLS_ISV_SVN={isv_svn} '
                                f'{debug_enclave_env_ver_ext}' + verifier_cert_mount_str + ' ' +
                                enc_keys_mount_str + ' -it verifier:latest')
        custom_image_dns_info = ''
        if config != 'test':
            custom_image_dns_info = ('. Assign the correct DNS information of the verifier server to'
                                     ' the environment variable SECRET_PROVISION_SERVERS')
        run_command = (f'{verifier_run_command} \n \n'
                       f'Execute below command to deploy the curated GSC image'
                       f'{custom_image_dns_info}:\n'
                       f'{workload_run.format(host_net, verifier_server, gsc_app_image)}')
    else:
        run_command = run_command_no_att.format(host_net, gsc_app_image)

    user_info = [image_ready_messg.format(gsc_app_image), commands_file + color_set,
                app_exit_messg]
    commands_fp.write(run_command)
    commands_fp.close()

    debug_help = [debug_run_messg, run_with_debug.format(workload_type, base_image_name),
                  extra_debug_instr.format(workload_type)]
    if debug_flag == 'y':
        debug_help = [extra_debug_instr.format(workload_type)]
    update_user_and_commentary_win_array(user_console, guide_win, user_info, debug_help)

    # Exit application with CTRL+G
    while (user_console.getch() != CTRL_G):
        continue
    return 0

wrapper(main, argv)
