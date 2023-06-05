import traceback

import boto3
import pathlib

import botocore.client
import unicodedata

import constants
import commons

archived_data_price_per_gb = 0.00099


def archive_command(root: pathlib.Path, aws_session: boto3.Session, user_id: str, command_data: str):
    """
    Upload all files with the given prefix as glacier 'DEEP_ARCHIVE' objects. Confirmation is
    required: all info about the files will be listed.
    :param root: The root folder path of the archive.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: Files will be archived under this relative path
    """
    if command_data == 'root':
        absolute_path = root
    else:
        absolute_path = root.joinpath(command_data)

    print(f'Files under "{absolute_path.as_posix()} will be archived."')
    print('Checking amount of files...')
    files_data = commons.get_files_data(root, absolute_path)
    print(f'Found a total of {files_data.file_count} files using {files_data.total_size_gb()} GB of space.')
    print(f'Estimated cost for archiving these files is {round(files_data.total_size_gb() * archived_data_price_per_gb, 5)}$ per month. '
          f'A one time upload cost will apply.')

    proceed = input('Are you sure you want to proceed with archiving these files? (Y)')
    if proceed == 'Y':
        print('Starting the upload of the selected files...')
        s3_client = aws_session.client('s3')
        __upload_files_to_archive(s3_client, user_id, files_data)
        print(f'Complete! Archived {files_data.file_count} files in your deep archive! Use "list_archive {command_data}" to see them.')
    else:
        print('Aborting the archive command...')


def __upload_files_to_archive(s3_client, user_id: str, data: commons.FilesData):
    progress = 0
    for file in data.files:
        key = f'{user_id}/{__sanitize_prefix(file["path_relative"])}'
        if not __object_already_exists(s3_client, key):
            try:
                s3_client.upload_file(
                    Filename=file['path_absolute'],
                    Bucket=constants.ARCHIVE_BUCKET_NAME,
                    Key=key,
                    ExtraArgs={
                        'StorageClass': 'DEEP_ARCHIVE'
                    }
                )
                progress += 1
                print(f'Uploaded {progress}/{data.file_count} files to archive... {round((progress / data.file_count) * 100, 2)}% complete')
            except botocore.client.ClientError:
                print(f'Failed to upload the file with key {key} to the archive.')
                traceback.print_exc()
        else:
            print(f'File with key {key} already exists in the archive: skipping it.')


def __sanitize_prefix(prefix: str):
    prefix = prefix.replace(' ', '_')
    prefix = unicodedata.normalize('NFKD', prefix)
    return prefix.encode('ASCII', 'ignore')


def __object_already_exists(s3_client, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=constants.ARCHIVE_BUCKET_NAME, Key=key)
        return True
    except botocore.client.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            print(f'Error: unable to check if object with key {key} exists or not. Assuming yes.')
            return True



# aws_session = boto3.Session()
# user_id = 'test_data'
# archive_command(pathlib.Path('C:\Programozas\Python\personal-deep-archive'), aws_session, user_id, command_data='app/test_data/')
