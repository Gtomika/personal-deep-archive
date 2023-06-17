import traceback
import multiprocessing

import boto3
import pathlib

import botocore.client
import unicodedata

import constants
import commons

archived_data_price_per_gb = 0.00099


def process_archive_command(root: pathlib.Path, aws_session: boto3.Session, user_id: str, command_data: str):
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
        print(f'Starting the upload of the selected files using {constants.THREADS} parallel processes')
        s3_client = aws_session.client('s3')
        __upload_files_to_archive(s3_client, user_id, files_data)
        print(f'Complete! Archived {files_data.file_count} files in your deep archive! Use "list_archive {command_data}" to see them.')
    else:
        print('Aborting the archive command...')


def __upload_files_to_archive(s3_client, user_id: str, data: commons.FilesData):
    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    for batched_files in commons.batch(data.files, constants.THREADS):
        # separate thread for the batched files
        thread_pool.apply_async(__upload_batch_to_archive, (s3_client, batched_files, user_id))
    thread_pool.close()
    thread_pool.join()


def __upload_batch_to_archive(s3_client, batched_files, user_id: str,):
    for file in batched_files:
        __upload_file_to_archive(s3_client, file, user_id)


def __upload_file_to_archive(s3_client, file, user_id: str):
    sanitized_prefix = __sanitize_prefix(file["path_relative"])
    key = f'{user_id}/{sanitized_prefix}'
    if not __object_already_exists(s3_client, key):
        try:
            s3_client.upload_file(
                Filename=file['path_absolute'],
                Bucket=constants.ARCHIVE_BUCKET_NAME,
                Key=key,
                ExtraArgs={
                    'StorageClass': constants.S3_DEEP_ARCHIVE
                }
            )
            print(
                f'Uploaded file with key {sanitized_prefix} to archive.')
        except botocore.client.ClientError:
            print(f'Failed to upload the file with key {sanitized_prefix} to the archive.')
            traceback.print_exc()
    else:
        print(f'File with key {sanitized_prefix} already exists in the archive: skipping it.')


def __sanitize_prefix(prefix: str):
    prefix = prefix.replace(' ', '_')
    return unicodedata.normalize('NFKD', prefix)


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

