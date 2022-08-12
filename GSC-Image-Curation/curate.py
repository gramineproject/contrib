#!/usr/bin/python
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import sys
from sys import argv
import textwrap
import time
import subprocess
import os
import os.path
from os import path
import docker
from constants import *

def initwindows():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    WHITE_AND_BLACK = curses.color_pair(1)
    WHITE_AND_BLUE = curses.color_pair(2)

    title_win = curses.newwin(title_height, title_width, 0, 0)
    user_console = curses.newwin(user_console_height, user_console_width, title_height, 0)
    guide_win = curses.newwin(guide_win_height, guide_win_width, title_height, int (screen_width/2))
    partition_win = curses.newwin(partition_height, partition_width, partition_y, int (sub_title_width) - 2)

    title_win.addstr(0, 0, " " * title_width, WHITE_AND_BLUE)
    title_win.addstr(0, int((title_width/2) - (len(title)/2)), title, WHITE_AND_BLUE | curses.A_BOLD)

    sub_win_title = 'User Agent (Start here)'
    sub_title_ind = 1

    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width) - (sub_title_width / 2) - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title, WHITE_AND_BLACK | curses.A_BOLD | curses.A_UNDERLINE)

    partition_win.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
    partition_win.refresh()

    sub_win_title = "Commentary"
    sub_title_ind = 2
    input_start_y, input_start_x = 2 , int((sub_title_ind * sub_title_width) - (sub_title_width / 2) - len(sub_win_title)/2)
    title_win.addstr(input_start_y, input_start_x, sub_win_title, WHITE_AND_BLACK | curses.A_BOLD | curses.A_UNDERLINE)
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
        win.addstr(f'Error: Could not fetch `{image_name}` image from dockerhub')
        win.addstr('Please check the image name is correct and try again.')
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
        [y, x] = user_console.getyx()
        user_console.addstr(y + line_offset, 0, textwrap.fill(user_text, user_console_width))
    
    for help_text in help_text_arr:
        [y, x] = guide_win.getyx()
        guide_win.addstr(y + line_offset, 0, textwrap.fill(help_text, guide_win_width))

    user_console.refresh()
    guide_win.refresh()

def update_user_error_win(user_console, error_text):
    [y, _] = user_console.getyx()
    user_console.addstr(y + 2, 0, textwrap.fill(error_text, user_console_width), curses.A_BOLD | curses.color_pair(3))
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
        editwin.addstr(start, 0, textwrap.fill(text_input, user_input_width), curses.color_pair(2) | curses.A_BOLD)
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
       gsc_image_with_debug='true'
       index_for_base_image_in_argv+=1
       index_for_test_flag_in_argv+=1
       min_length_of_argv+=1

    # Acquiring Base image type and name from user input
    base_image_input=argv[index_for_base_image_in_argv]
    if '/' in base_image_input:
        base_image_type=base_image_input.split('/', maxsplit=1)[0]
        base_image_name=base_image_input.split('/', maxsplit=1)[1]
        if base_image_type is '' or  base_image_name is '':
            print_correct_usage(argv[0])
    else:
         print_correct_usage(argv[0])

    docker_socket = docker.from_env()
    base_image = get_docker_image(docker_socket, base_image_name)
    if base_image is None:
        stdscr.addstr(f'Warning: Cannot find application Docker image `{base_image_name}`.\n')
        stdscr.addstr('Fetching from Docker Hub ...\n')
        if pull_docker_image(stdscr, docker_socket, base_image_name) == -1:
            stdscr.getch()
        return 1

    log_file = f'{base_image_type}.log'
    log_file_pointer = open(log_file, 'w')

    gsc_app_image ='gsc-{}'.format(base_image_name)

    # Generating Test Image
    if len(argv) > min_length_of_argv:
        if argv[index_for_test_flag_in_argv]:
            stdscr.addstr('Your test GSC image is being generated. This image is not supposed to be used in production \n\n')
            stdscr.refresh()
            subprocess.call(["./curation_script.sh", base_image_type, base_image_name, "test-key",
                '', "test-image", gsc_image_with_debug], stdout=log_file_pointer, stderr=log_file_pointer)
            check_image_creation_success(stdscr, docker_socket,gsc_app_image,log_file)
            stdscr.addstr(f'Run the {gsc_app_image} docker image using the below command. Host networking (--net=host) is optional\n')
            stdscr.addstr(f'docker run --net=host --device=/dev/sgx/enclave -it {gsc_app_image}')
            stdscr.getch()
            return 1

    user_console, guide_win = initwindows()

    update_user_and_commentary_win_array(user_console, guide_win, introduction, index)
    update_user_input()

    update_user_and_commentary_win_array(user_console, guide_win, key_prompt, signing_key_help)
    key_path = fetch_file_from_user('', 'test-key', user_console)

    debug_enclave_command_for_verifier=''
    if key_path == 'test-key':
        debug_enclave_command_for_verifier='-e RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 -e RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1'

#   Remote Attestation with RA-TLS
    update_user_and_commentary_win_array(user_console, guide_win, server_ca_cert_prompt, server_ca_help)
    attestation_input = update_user_input()
    ca_cert_path = ''
    attestation_required = ''
    if attestation_input == 'done':
        attestation_required = 'y'
        ca_cert_path = fetch_file_from_user('verifier_image/ssl/ca.crt', '', user_console)
        server_cert_path = fetch_file_from_user('verifier_image/ssl/server.crt', '', user_console)
        server_key_path = fetch_file_from_user('verifier_image/ssl/server.key', '', user_console)

    if attestation_input == 'test':
        ca_cert_path='verifier_image/ca.crt'

    if ca_cert_path:
        os.chdir('verifier_image')
        verifier_log_file = 'verifier.log'
        verifier_log_file_pointer = open(verifier_log_file, 'w')
        update_user_and_commentary_win_array(user_console, guide_win, ['Building the RA-TLS Verifier image, this might take couple of minutes'],
         [f'You may monitor verifier_image/{verifier_log_file} for progress'])
        proc = subprocess.call(['./verifier_helper_script.sh', 'attestation_required'], shell=True, stdout=verifier_log_file_pointer, stderr=verifier_log_file_pointer)
        os.chdir('../')
        check_image_creation_success(user_console, docker_socket,'verifier_image:latest', 'verifier_image/'+verifier_log_file)

#   Provide arguments
    update_user_and_commentary_win_array(user_console, guide_win, arg_input, arg_help)
    args = update_user_input()

#   Provide enviroment variables
    update_user_and_commentary_win_array(user_console, guide_win, env_input, env_help)
    env_required = 'n'
    envs = update_user_input()
    if envs:
        env_required = 'y'

#   Provide encrypted files
    update_user_and_commentary_win_array(user_console, guide_win, encrypted_files_prompt, encypted_files_help)
    encrypted_files = update_user_input()

#   Provide encryption key
    ef_required = 'n'
    if encrypted_files:
        encryption_key_prompt = 'Please provide the path to the key used for the encryption.'
        edit_user_win(user_console, encryption_key_prompt)
        encryption_key = fetch_file_from_user('', '', user_console)
        ef_required = 'y'

    update_user_and_commentary_win_array(user_console, guide_win, wait_message, [f'You may monitor {base_image_type}/gsc.log for detailed progress'])

    subprocess.call(['./curation_script.sh', base_image_type, base_image_name, key_path, args,
                  attestation_required, ca_cert_path, env_required, envs, ef_required,
                  encrypted_files, gsc_image_with_debug], stdout=log_file_pointer, stderr=log_file_pointer)
    check_image_creation_success(user_console, docker_socket, gsc_app_image, log_file)

    if attestation_required == 'y':
        run_command = ['The curated GSC image, and the remote attestation and secrets provisioning verifier image is ready.' \
                    'To run these images with host networking enabled (--net=host), start the verifier and GSC image in the order shown in the blue box.']
        run_command = [f'docker run --net=host {debug_enclave_command_for_verifier} --device=/dev/sgx/enclave  -it verifier_image:latest {encryption_key}',
                f'docker run --device=/dev/sgx/enclave -e SECRET_PROVISION_SERVERS=<server-dns_name:port> -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -it {gsc_app_image}']
    else:
        user_info = [f'The curated GSC image image is ready.', \
                     f'You can run the {gsc_app_image} using the following command. Host networking (--net=host) is optional']
        run_command = [f'docker run --net=host --device=/dev/sgx/enclave -it {gsc_app_image}']

    debug_help = [f'Run with debug (-d) enabled to get more information in the event of failures during runtime:', f'python curate.py -d {base_image_type}/{base_image_name}' \
     f"It's also possible that you run into issues resulting from lack of sufficient enclave memory pages, or insufficient number of threads. The {base_image_type}.manifest can be " \
          "modified to change the defaults"]
    update_user_and_commentary_win_array(user_console, guide_win, user_info, debug_help) 
    update_run_win(run_command)
    user_console.getch()

wrapper(main, argv)
