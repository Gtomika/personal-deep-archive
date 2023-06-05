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


def extract_command_arguments(command: str) -> str:
    return command.split(sep=' ')[1]


# getting path to the archive root on this machine
if path.isfile('paths.json'):
    print('Reading root directory from file...')
    with open('paths.json', 'r') as paths_file:
        paths_data = json.load(paths_file)
        root_directory = paths_data['root']
else:
    root_directory = input(f'Provide the root directory of your archive, such as "C:/data/archive"')
root_directory_path = pathlib.Path(root_directory)


# command processing flow
command = 'help'
while command != 'exit':
    print("\n\n")
    try:
        if command == 'help':
            help_command.help_command(user_data.email)
        elif command.startswith('list_archive '):
            list_command.process_list_archive_command(aws_session, user_data.user_id, extract_command_arguments(command))
        elif command.startswith('list_restored '):
            list_command.process_list_restored_command(aws_session, user_data.user_id, extract_command_arguments(command))
        elif command.startswith('archive_data '):
            archive_command.archive_command(root_directory_path, aws_session, user_data.user_id, extract_command_arguments(command))
        elif command.startswith('restore_data '):
            restore_command.restore_command(aws_session, user_data.user_id, extract_command_arguments(command))
        elif command.startswith('download_data '):
            download_command.download_command(root_directory_path, aws_session, user_data.user_id, extract_command_arguments(command))
        else:
            print('Error: this command is unknown')
    except BaseException as e:
        print('An error prevented your command from running. You may have used an invalid command.')
        traceback.print_exc()
    command = input('\n\nEnter your next command or "exit" to stop the program: ')


