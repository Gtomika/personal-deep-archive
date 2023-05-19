import boto3

import login
import list_command
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

# command processing flow
command = 'list_archive root'
while command != 'exit':
    print("\n\n")
    if command.startswith('list_archive '):
        prefix = command.split(sep=' ')[1]
        list_command.process_list_archive_command(aws_session, user_data.user_id, prefix)
    elif command.startswith('list_restored '):
        prefix = command.split(sep=' ')[1]
        list_command.process_list_restored_command(aws_session, user_data.user_id, prefix)
    else:
        print('Error: this command is unknown')
    command = input('\n\nEnter your next command or "exit" to stop the program: ')



