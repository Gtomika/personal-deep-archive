import traceback
import pathlib

import boto3
import botocore.client

import commons
import constants


def download_command(root_directory: pathlib.Path, aws_session: boto3.Session, user_id: str, command_data: str):
    """
    Allows to download restored files. Can take 'root' or a prefix, to filter which restored
    files to download.
    """
    print(f'Checking the objects with prefix {command_data}')
    full_prefix, internal_prefix = commons.create_restored_prefix_with_user_id(user_id, command_data)
    download_path = __create_download_folder_path(root_directory)

    s3_client = aws_session.client('s3')
    object_count = commons.count_objects_with_prefix(s3_client, full_prefix, 'STANDARD')

    print(f'A total of {object_count.count} objects will be downloaded, with total size of {object_count.total_size_in_gb()} GB!')
    print(f'The downloaded files will be placed under {download_path.as_posix()}, in your selected root directory.')
    print(f'A one time download fee will apply, depending on the size.')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print('Starting the download of all selected objects. This will take some time...')
        downloads_completed = __download_objects(s3_client, object_count.pages, download_path, internal_prefix, object_count.count)
        print(f'Download of the selected objects finished. {downloads_completed}/{object_count.count} downloads were successfully completed.')
    else:
        print('Aborting download...')


def __download_objects(s3_client, pages, download_path: pathlib.Path, internal_prefix: str, total_files: int) -> int:
    downloads_success = 0
    downloads_total = 0
    for page in pages:
        if 'Contents' in page:
            for s3_object in page['Contents']:
                try:
                    key = s3_object['Key']
                    object_download_path = __create_download_path_for_object(download_path, key, internal_prefix)
                    s3_client.download_file(
                        Bucket=constants.ARCHIVE_BUCKET_NAME,
                        Key=key,
                        Filename=object_download_path
                    )
                    downloads_success += 1
                    downloads_total += 1
                    progress = round((downloads_total/total_files)*100, 3)
                    print(f'The object "{key}" has been downloaded to "{object_download_path}. Progress: {progress}%"')
                except botocore.client.ClientError:
                    print(f'Failed to download S3 object with key {s3_object["Key"]}')
                    traceback.print_exc()
                    downloads_total += 1
    return downloads_success


def __create_download_folder_path(root: pathlib.Path) -> pathlib.Path:
    """
    Create path to the download directory. This method also ensures that the folder exists
    """
    download_dir = root.joinpath(constants.DOWNLOAD_FOLDER)
    if not download_dir.exists():
        download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def __create_download_path_for_object(download_path: pathlib.Path, s3_key: str, internal_prefix: str) -> str:
    """
    Converts the S3 key of the object into a path where it will be downloaded. The folder
    structure is based on the prefix.
    :param internal_prefix The 'common' prefix such as user ID, that should not be reflected in the local directory structure
    """
    prefix_of_interest = s3_key.removeprefix(internal_prefix)
    return download_path.joinpath(prefix_of_interest).as_posix()


