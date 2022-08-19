#!/usr/bin/python

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
from constants import *
from curses import wrapper
from curses.textpad import Textbox, rectangle
from glob import escape
from os import path
from sys import argv

def initwindows():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    WHITE_AND_BLACK = curses.color_pair(1)
    WHITE_AND_BLUE = curses.color_pair(2)

    title_win = curses.newwin(title_height, title_width, 0, 0)
    user_console = curses.newwin(user_console_height, user_console_width, title_height, 0)
    guide_win = curses.newwin(guide_win_height, guide_win_width, title_height, int (screen_width/2))
    partition_win = curses.newwin(partition_height, partition_width, partition_y, \
        int (sub_title_width) - 2)

    title_win.addstr(0, 0, " " * title_width, WHITE_AND_BLUE)
    title_win.addstr(0, int((title_width/2) - (len(title)/2)), title, WHITE_AND_BLUE | curses.A_BOLD)

    sub_win_title = user_win_title
    sub_title_ind = 1

    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width) - (sub_title_width / 2) \
        - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title, WHITE_AND_BLACK | curses.A_BOLD | \
        curses.A_UNDERLINE)

    partition_win.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    partition_win.refresh()

    sub_win_title = help_win_title
    sub_title_ind = 2
    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width) - (sub_title_width / 2) \
        - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title, WHITE_AND_BLACK | curses.A_BOLD | \
        curses.A_UNDERLINE)
    title_win.refresh()
    return(user_console, guide_win)

def resize_screen(screen_height, screen_width):
    subprocess.call(["echo","-e",f"\x1b[8;{screen_height};{screen_width}t"])
    time.sleep(0.35)

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

def print_correct_usage(win, arg):
    win.addstr(f'Usage: {arg} <redis/redis:7.0.0> (for custom image)\n')
    win.addstr(f'Usage: {arg} <redis/redis:7.0.0> test (for test image)\n\n')
    win.addstr('Press any key to exit')
    win.getch()
    sys.exit(1)

def get_docker_image(docker_socket, image_name):
    try:
        docker_image = docker_socket.images.get(image_name)
        return docker_image
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        return None

def update_user_input():
    editwin = curses.newwin(user_input_height, user_input_width, user_input_start_y, 0)
    editwin.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    box = Textbox(editwin)
    box.edit()
    editwin.refresh()
    return(box.gather().strip().replace("\n", ""))

def fetch_file_from_user(file, default, user_console):
    if file:
        while not path.exists(file):
            error = f'Error: {file} file does not exist. Please follow instructions above'
            update_user_error_win(user_console, error)
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
        user_console.addstr(y + line_offset, 0, textwrap.fill(user_text, user_console_width), color)
    
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
    user_console.addstr(y + 2, 0, textwrap.fill(error_text, user_console_width), curses.A_BOLD \
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
        editwin.addstr(start, 0, textwrap.fill(text_input, user_input_width), curses.color_pair(2) \
            | curses.A_BOLD)
        start = start + 2

    editwin.refresh()

def main(stdscr, argv):
    stdscr.clear()
    resize_screen(screen_height, screen_width)
    stdscr = curses.initscr()

    if len(argv) < 2:
        print_correct_usage(stdscr, argv[0])

    gsc_image_with_debug='false'
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
        if base_image_type is '' or  base_image_name is '':
            print_correct_usage(argv[0])
    else:
         print_correct_usage(argv[0])

    docker_socket = docker.from_env()
    base_image = get_docker_image(docker_socket, base_image_name)
    if base_image is None:
        stdscr.addstr(f'Warning: Cannot find application Docker image `{base_image_name}`.\n')
        stdscr.addstr('Fetching from Docker Hub ...\n')
        stdscr.refresh()
        if pull_docker_image(stdscr, docker_socket, base_image_name) == -1:
            stdscr.getch()
            return 1

    log_file_name, n = re.subn('[:/]', '_', base_image_name)
    log_file = f'{base_image_type}/{log_file_name}.log'
    log_file_pointer = open(log_file, 'w')

    gsc_app_image ='gsc-{}'.format(base_image_name)

    # Generating Test Image
    if len(argv) > min_length_of_argv:
        if argv[index_for_test_flag_in_argv]:
            stdscr.addstr('Your test GSC image is being generated. This image is not supposed to be'
                'used in production \n\n')
            stdscr.refresh()
            subprocess.call(["./curation_script.sh", base_image_type, base_image_name, "test-key",
                '', "test-image", gsc_image_with_debug], stdout=log_file_pointer, \
                    stderr=log_file_pointer)
            check_image_creation_success(stdscr, docker_socket,gsc_app_image,log_file)
            stdscr.addstr(f'Run the {gsc_app_image} docker image in an Azure Confidential Compute '
            'instance using the below command. Host networking (--net=host) is optional\n')
            stdscr.addstr(f'docker run --net=host --device=/dev/sgx/enclave -it {gsc_app_image}')
            stdscr.getch()
            return 1

    user_console, guide_win = initwindows()

    update_user_and_commentary_win_array(user_console, guide_win, introduction, index)
    update_user_input()

    kernel_name=subprocess.check_output(["uname -r"],encoding='utf8',shell=True)
    if 'azure' not in kernel_name:
        update_user_and_commentary_win_array(user_console, guide_win, ['Warning: You are building '
        'these images on an non Azure Confidential Compute instance' + color_set, 'Please ensure you run the '
        'final images on an Azure VM or in the AKS cluster only', 'Press CTRL+G to continue'],
        ['The target deployment environment is assumed to be an Azure Confidential compute instance'
            ' with out of tree DCAP driver'])
        update_user_input()

#   Obtain enclave signing key
    update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
    key_path = fetch_file_from_user('', 'test-key', user_console)
    debug_enclave_command_for_verifier=''
    if key_path == 'test-key':
        debug_enclave_command_for_verifier='-e RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 -e '
        'RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1'

#   Remote Attestation with RA-TLS
    update_user_and_commentary_win_array(user_console, guide_win, server_ca_cert_prompt, \
        server_ca_help)
    attestation_input = update_user_input()
    ca_cert_path = ''
    attestation_required = ''
    if attestation_input == 'done':
        ca_cert_path = fetch_file_from_user('verifier_image/ssl/ca.crt', '', user_console)
        server_cert_path = fetch_file_from_user('verifier_image/ssl/server.crt', '', \
            user_console)
        server_key_path = fetch_file_from_user('verifier_image/ssl/server.key', '', \
            user_console)

    if attestation_input == 'test':
        ca_cert_path='verifier_image/ca.crt'


    if ca_cert_path:
        attestation_required = 'y'
        os.chdir('verifier_image')
        verifier_log_file = 'verifier.log'
        verifier_log_file_pointer = open(verifier_log_file, 'w')
        update_user_and_commentary_win_array(user_console, guide_win, ['Building the RA-TLS Verifier'
        ' image, this might take couple of minutes'],
         [f'You may monitor verifier_image/{verifier_log_file} for progress'])
        proc = subprocess.call(['./verifier_helper_script.sh', 'attestation_required'], shell=True, \
            stdout=verifier_log_file_pointer, stderr=verifier_log_file_pointer)
        os.chdir('../')
        check_image_creation_success(user_console, docker_socket,'verifier_image:latest', \
            'verifier_image/'+verifier_log_file)

#   Provide arguments
    update_user_and_commentary_win_array(user_console, guide_win, arg_input, arg_help)
    args = update_user_input()

#   Provide enviroment variables
    update_user_and_commentary_win_array(user_console, guide_win, env_input, env_help)
    env_required = 'n'
    envs = update_user_input()
    if envs:
        env_required = 'y'

    ef_required = 'n'
    encryption_key = ''
    encrypted_files = ''
    if attestation_required == 'y':
    #   Provide encrypted files
        update_user_and_commentary_win_array(user_console, guide_win, encrypted_files_prompt, \
            encypted_files_help)
        encrypted_files = update_user_input()

    #   Provide encryption key
        if encrypted_files:
            encryption_key_prompt = 'Please provide the path to the key used for the encryption.'
            edit_user_win(user_console, encryption_key_prompt)
            encryption_key = fetch_file_from_user('', '', user_console)
            ef_required = 'y'

    update_user_and_commentary_win_array(user_console, guide_win, wait_message, \
        [f'You may monitor {log_file} for detailed progress'])
    subprocess.call(['./curation_script.sh', base_image_type, base_image_name, key_path, args,
                  attestation_required, ca_cert_path, env_required, envs, ef_required,
                  encrypted_files, gsc_image_with_debug], stdout=log_file_pointer, stderr=log_file_pointer)
    check_image_creation_success(user_console, docker_socket, gsc_app_image, log_file)

    if attestation_required == 'y':
        user_info = ['The curated GSC image, and the remote attestation and secrets provisioning '
        'verifier image is ready. To run these images with host networking enabled (--net=host), '
        'start the verifier and GSC image in separate terminals in the order shown in the blue box.']
        key_name_and_path=encryption_key.rsplit('/',1)
        run_command = [f'docker run --net=host {debug_enclave_command_for_verifier} '
        f'--device=/dev/sgx/enclave -v {key_name_and_path[0]}:/keys -it verifier_image:latest '
        f'/keys/{key_name_and_path[1]}',
        f'docker run --device=/dev/sgx/enclave -e SECRET_PROVISION_SERVERS=<server-dns_name:port> '
        f'-v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -it {gsc_app_image}']
    else:
        user_info = [f'The curated GSC image image is ready.', f'You can run the {gsc_app_image} '
        'using the following command. Host networking (--net=host) is optional', 'Press CTRL+G to exit the '
        'application']
        run_command = [run_command_no_att.format(gsc_app_image)]

    debug_help = ['Run with debug (-d) enabled to get more information in the event of failures '
    'during runtime:', run_with_debug.format(base_image_type, base_image_name), extra_debug_instr.format(base_image_type)]
    update_user_and_commentary_win_array(user_console, guide_win, user_info, debug_help)
    update_run_win(run_command)

    while (user_console.getch() != 7):
        continue

wrapper(main, argv)
