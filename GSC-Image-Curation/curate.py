#!/usr/bin/python
# This script will provide step-by-step guidance in creating your own custom Docker images protected
# by Gramine. User will be prompted for input at every stage, and once the script has all
# the details, it will call a separate curation script (util/curation_script.sh) that takes the
# user provided inputs to create the graminized Docker image using GSC. This script also calls into
# a script to generate the verifier Docker image (for SGX remote attestation). The generated
# verifier Docker image is supposed to be started together with the graminized Docker image, to
# verify the SGX attestation evidence (SGX quote) sent by the latter image.

# Following are the command line parameters accepted by this file:
# - '<type of workload>/<base image to be graminized>' For eg redis/redis:7.0.0
# - 'test' : to generate a test image (for learning purposes) with a test enclave signing key.
# - '-d'    : to generate a debug graminized container helpful for debugging issues.

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
from curses import wrapper
from curses.textpad import Textbox, rectangle
from glob import escape
from os import path
from sys import argv

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

    title_win.addstr(0, 0, " " * title_width, WHITE_AND_BLUE)
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
    subprocess.call(["echo","-e",f"\x1b[8;{screen_height};{screen_width}t"])
    time.sleep(0.35)

def print_correct_usage(win, arg):
    win.addstr(f'Usage: {arg} <redis/redis:7.0.0> (for custom image)\n')
    win.addstr(f'Usage: {arg} <redis/redis:7.0.0> test (for test image)\n\n')
    win.addstr('Press any key to exit')
    win.getch()
    sys.exit(1)

def update_user_input():
    editwin = curses.newwin(user_input_height, user_input_width, user_input_start_y, 0)
    editwin.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    box = Textbox(editwin)
    box.edit()
    editwin.refresh()
    user_input = box.gather().strip().replace("\n", "")
    editwin.erase()
    editwin.refresh()
    return(user_input)

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
        if (user_text.find(color_set) >= 0):
            color = curses.color_pair(2) | curses.A_REVERSE
            user_text = user_text.replace(color_set , '')
        [y, x] = user_console.getyx()
        user_console.addstr(y + line_offset, 0, textwrap.fill(user_text, user_console_width),
         color)
    
    for help_text in help_text_arr:
        color = 0
        if (help_text.find(color_set) >= 0):
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
        win.addstr(f'For more info, look at the logs file here: {log_file}')
        win.getch()
        sys.exit(1)

def pull_docker_image(win, docker_socket, image_name):
    try:
        docker_image = docker_socket.images.pull(image_name)
        return 0
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        win.addstr(f'Error: Could not fetch `{image_name}` image from dockerhub \n')
        win.addstr('Please check the image name is correct and try again.')
        win.refresh()
        return -1

def fetch_file_from_user(file, default, user_console):
    if file:
        while not path.exists(file):
            update_user_error_win(user_console, file_nf_error.format(file))
            update_user_input()
        return file
    file = update_user_input()
    while not path.exists(file):
        if(len(file) == 0):
            if default:
                file = default
                return file
        error = f'Error: {file} file does not exist.'
        update_user_error_win(user_console, error)
        file = update_user_input()
    return file

# User is expected to provide the path to a signing key, or either of the below
# - 'n' = amounts to 'no-sign' which means the curated GSC image will be an unsigned image, that
#         the user can sign later on.
# - no input will result in the generation of a test key. The image hence generated should not be
#   used in production.
def get_enclave_signing_input(user_console):
    sign_file = ''
    while not path.exists(sign_file):
        sign_file = update_user_input()
        if sign_file == 'n':
            key_path = 'no-sign'
            return key_path
        elif sign_file == '':
            key_path = 'test-key'
            return key_path
        else:
            update_user_error_win(user_console, file_nf_error.format(sign_file))
    return sign_file

def get_attestation_input(user_console):
    attestation_input = update_user_input()
    while True:
        while (attestation_input not in ['test', 'done', '']):
            update_user_error_win(user_console, 'Invalid option specified')
            attestation_input = update_user_input()
        if attestation_input == 'done':
            if (path.exists('verifier/ssl/ca.crt')
             and path.exists('verifier/ssl/server.crt')
             and path.exists('verifier/ssl/server.key')):
                return attestation_input
            update_user_error_win(user_console, 'One or more files does not exist at'
            ' verifier/ssl/ directory')
            attestation_input = update_user_input()
            continue
        return attestation_input

def main(stdscr, argv):
    stdscr.clear()
    resize_screen(screen_height, screen_width)
    stdscr = curses.initscr()

    if len(argv) < 2:
        print_correct_usage(stdscr, argv[0])

    gsc_image_with_debug = 'false'
    index_for_base_image_in_argv = 1
    index_for_test_flag_in_argv = 2
    # min length of argv is the length of argv without test flag
    min_length_of_argv = 2

    # Checking if debug flag is specified by the user
    if argv[1] == '-d':
       gsc_image_with_debug ='true'
       index_for_base_image_in_argv += 1
       index_for_test_flag_in_argv += 1
       min_length_of_argv += 1

    # Acquiring Base image type and name from user input
    base_image_input = argv[index_for_base_image_in_argv]
    if '/' in base_image_input:
        base_image_type = base_image_input.split('/', maxsplit=1)[0]
        base_image_name = base_image_input.split('/', maxsplit=1)[1]
        if base_image_type == '' or  base_image_name == '':
            print_correct_usage(argv[0])
    else:
         print_correct_usage(argv[0])

    docker_socket = docker.from_env()
    base_image = get_docker_image(docker_socket, base_image_name)
    if base_image is None:
        stdscr.addstr(image_not_found_warn.format(base_image_name))
        stdscr.refresh()
        if pull_docker_image(stdscr, docker_socket, base_image_name) == -1:
            stdscr.getch()
            return 1

    log_file_name, n = re.subn('[:/]', '_', base_image_name)
    log_file = f'{base_image_type}/{log_file_name}.log'
    log_file_pointer = open(log_file, 'w')

    gsc_app_image ='gsc-{}'.format(base_image_name)
    gsc_app_image_unsigned ='gsc-{}-unsigned'.format(base_image_name)

    # Generating Test Image
    if len(argv) > min_length_of_argv:
        if argv[index_for_test_flag_in_argv]:
            stdscr.addstr(test_image_mssg)
            stdscr.refresh()
            subprocess.call(["util/curation_script.sh", base_image_type, base_image_name,
             "test-key", '', "test-image", gsc_image_with_debug], stdout=log_file_pointer,
              stderr=log_file_pointer)
            check_image_creation_success(stdscr, docker_socket,gsc_app_image,log_file)
            stdscr.addstr(test_run_instr.format(gsc_app_image, gsc_app_image))
            stdscr.getch()
            return 1

    user_console, guide_win = initwindows()

    update_user_and_commentary_win_array(user_console, guide_win, introduction, index)
    update_user_input()

    kernel_name=subprocess.check_output(["uname -r"],encoding='utf8',shell=True)
    if 'azure' not in kernel_name:
        update_user_and_commentary_win_array(user_console, guide_win, azure_warning, azure_help)
        update_user_input()

    # Obtain Distro version
    update_user_and_commentary_win_array(user_console, guide_win, distro_prompt, distro_help)
    distro_option = update_user_input()
    distro = 'Ubuntu:18.04'
    if distro_option == '2':
        distro = 'Ubuntu:20.04'

    # Obtain enclave signing key
    update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
    key_path = get_enclave_signing_input(user_console)
    config = ''
    if key_path == 'test-key':
        config = 'test'

    # Remote Attestation with RA-TLS
    update_user_and_commentary_win_array(user_console, guide_win, attestation_prompt,
     attestation_help)

    attestation_input = get_attestation_input(user_console)
    ca_cert_path = ''
    verifier_server = '<verifier-dns-name:port>'
    attestation_required = ''
    host_net = ''
    if attestation_input == 'done':
        attestation_required = 'y'
        ca_cert_path = ssl_folder_path_on_host+'/ca.crt'

    if attestation_input == 'test':
        ca_cert_path, verifier_server = ssl_folder_path_on_host+'/ca.crt', '"localhost:4433"'
        host_net, config = '--net=host', 'test'
        attestation_required = 'y'

    # Provide arguments
    update_user_and_commentary_win_array(user_console, guide_win, arg_input, arg_help)
    args = update_user_input()

    # Provide enviroment variables
    update_user_and_commentary_win_array(user_console, guide_win, env_input, env_help)
    env_required = 'n'
    envs = update_user_input()
    if envs:
        env_required = 'y'

    ef_required = 'n'
    encryption_key = ''
    enc_key_path_in_verifier = ''
    encrypted_files = ''
    if attestation_required == 'y':
        # Provide encrypted files
        update_user_and_commentary_win_array(user_console, guide_win, encrypted_files_prompt,
         encypted_files_help)
        encrypted_files = update_user_input()

        # Provide encryption key
        if encrypted_files:
            edit_user_win(user_console, encryption_key_prompt)
            encryption_key = fetch_file_from_user('', '', user_console)
            encryption_key_name = os.path.basename(encryption_key)
            enc_key_path_in_verifier = enc_key_path.format(encryption_key_name)
            ef_required = 'y'

    if ca_cert_path:
        os.chdir('verifier')
        verifier_log_file_pointer = open(verifier_log_file, 'w')
        update_user_and_commentary_win_array(user_console, guide_win, [verifier_build_messg],
         [verifier_log_help.format(verifier_log_file)])
        subprocess.call(['./verifier_helper_script.sh', attestation_input,
         enc_key_path_in_verifier], stdout=verifier_log_file_pointer,
         stderr=verifier_log_file_pointer)
        os.chdir('../')
        check_image_creation_success(user_console, docker_socket,'verifier:latest',
         'verifier/'+verifier_log_file)

    update_user_and_commentary_win_array(user_console, guide_win, wait_message,
     [log_progress.format(log_file)])
    subprocess.call(['util/curation_script.sh', base_image_type, base_image_name, key_path, args,
     attestation_required, ca_cert_path, env_required, envs, ef_required, encrypted_files,
     gsc_image_with_debug], stdout=log_file_pointer, stderr=log_file_pointer)
    image = gsc_app_image
    if key_path == 'no-sign':
        image = gsc_app_image_unsigned
    check_image_creation_success(user_console, docker_socket, image, log_file)

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

        verifier_run_command = (f'docker run --rm {host_net} --device=/dev/sgx/enclave '
         f'{debug_enclave_env_ver_ext}' + verifier_cert_mount_str + ' ' + enc_keys_mount_str
         + ' -it verifier:latest')
        run_command = (f'{verifier_run_command} \n \n'
         f'{workload_run.format(host_net, verifier_server, gsc_app_image)}')
    else:
        run_command = run_command_no_att.format(host_net, gsc_app_image)

    user_info = [image_ready_messg.format(gsc_app_image), commands_file + color_set,
     app_exit_messg]
    if key_path == 'no-sign':
        commands_fp.write(sign_instr.format(base_image_name))
    commands_fp.write(run_command)
    commands_fp.close()

    debug_help = [debug_run_messg, run_with_debug.format(base_image_type, base_image_name),
                  extra_debug_instr.format(base_image_type)]
    update_user_and_commentary_win_array(user_console, guide_win, user_info, debug_help)

    # Exit application with CTRL+G
    while (user_console.getch() != CTRL_G):
        continue

wrapper(main, argv)
