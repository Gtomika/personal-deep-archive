import json
import traceback

import boto3
import pathlib
import os.path as path

import login
import help_command
import list_command
import archive_command
import restore_command
import download_command
import constants
from commons import extract_command_arguments, get_files_data, extract_quoted_argument


if __name__ == '__main__':
    # login flow
    print('Sign in to access your archive!')
    username, password = login.obtain_user_credentials()
    user_data = login.log_in(username=username, password=password)
    if user_data is not None:
        cognito_identity_id = login.get_cognito_identity_id(user_data.id_token)
        user_data.set_user_id(cognito_identity_id)
        print(f'Login successful, your user ID is {user_data.user_id}')

        access_key_id, secret_key, session_token = login.exchange_token_for_aws_credentials(cognito_identity_id, user_data.id_token)
        print('Temporary AWS credentials have been obtained!')
    else:
        print('The authentication was unsuccessful, aborting...')
        exit(1)

    aws_session = boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=constants.AWS_REGION
    )

    # getting path to the archive root on this machine
    if path.isfile('paths.json'):
        with open('paths.json', 'r') as paths_file:
            paths_data = json.load(paths_file)
            root_directory = paths_data['root']
            print(f'Read root directory from file, it is {root_directory}')
    else:
        root_directory = input(f'Provide the root directory of your archive, such as "C:/data/archive"')
    root_directory_path = pathlib.Path(root_directory)
    root_data = get_files_data(root_directory_path, root_directory_path)
    print(f'The root directory contains a total of {root_data.file_count} files with a total size of {root_data.total_size_gb()} GBs')

    # command processing flow
    command = 'help'
    while command != 'exit':
        print("\n\n")
        try:
            if command == 'help':
                help_command.process_help_command(user_data.email)
            elif command.startswith('list_archive '):
                list_command.process_list_archive_command(aws_session, user_data.user_id, extract_command_arguments(command))
            elif command.startswith('archive_data '):
                archive_command.process_archive_command(root_directory_path, aws_session, user_data.user_id, extract_quoted_argument(command))
            elif command.startswith('restore_data '):
                restore_command.process_restore_command(aws_session, user_data.user_id, extract_command_arguments(command))
            elif command.startswith('download_data '):
                download_command.process_download_command(root_directory_path, aws_session, user_data.user_id, extract_command_arguments(command))
            else:
                print('Error: this command is unknown')
        except BaseException as e:
            print('An error prevented your command from running. You may have used an invalid command.')
            traceback.print_exc()
        command = input('\n\nEnter your next command or "exit" to stop the program: ')




