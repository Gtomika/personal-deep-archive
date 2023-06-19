import traceback
import pathlib
import multiprocessing
import threading

import boto3
import botocore.client

import commons
import constants


def process_download_command(root_directory: pathlib.Path, aws_session: boto3.Session, user_id: str, command_data: str):
    print(f'Checking the objects with prefix {command_data}')
    full_prefix, internal_prefix = commons.create_prefix_with_user_id(user_id, command_data)
    download_path = __create_download_folder_path(root_directory)

    s3_client = aws_session.client('s3')
    object_count = commons.count_objects_with_prefix(s3_client, full_prefix)

    print(f'A total of {object_count.count} objects will be downloaded, with total size of {object_count.total_size_in_gb()} GB!')
    print(f'The downloaded files will be placed under {download_path.as_posix()}, in your selected root directory.')
    print(f'A one time download fee will apply, depending on the size.')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print(f'Starting the download of all selected objects using {constants.THREADS} parallel processes. This will take some time...')
        downloads_completed = __download_objects(aws_session, object_count.pages, download_path, internal_prefix, object_count.count)
        print(f'Download of the selected objects finished. {downloads_completed}/{object_count.count} downloads were successfully completed.')
    else:
        print('Aborting download...')


download_progress = 0
download_success = 0


def __download_objects(
        aws_session: boto3.Session,
        pages,
        download_path: pathlib.Path,
        internal_prefix: str,
        total_files: int
) -> int:
    global download_progress, download_success

    download_success = 0
    download_progress = 0

    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    lock = threading.Lock()

    for page in pages:
        thread_pool.apply_async(__download_object_page, (aws_session, page, download_path, internal_prefix, total_files, lock))

    thread_pool.close()
    thread_pool.join()

    return download_success


def __download_object_page(
        aws_session: boto3.Session,
        page,
        download_path: pathlib.Path,
        internal_prefix: str,
        total_files: int,
        lock: threading.Lock
):
    global download_success

    s3_client = aws_session.client('s3')
    if 'Contents' in page:
        for s3_object in page['Contents']:
            key = s3_object['Key']
            user_friendly_key = key.removeprefix(internal_prefix)
            absolute_path = download_path.joinpath(user_friendly_key)
            progress_percent = __update_progress(lock, total_files)
            try:
                with __create_download_file_for_object(absolute_path) as download_file:
                    s3_client.download_fileobj(
                        Bucket=constants.ARCHIVE_BUCKET_NAME,
                        Key=key,
                        Fileobj=download_file
                    )
                with lock:
                    download_success += 1
                print(f'The object "{user_friendly_key}" has been downloaded. {progress_percent}% complete.')
            except s3_client.exceptions.InvalidObjectState:
                print(f'The object "{user_friendly_key}" has NOT BEEN RESTORED, and so it cannot be downloaded. {progress_percent}% complete.')
                __delete_empty_file(absolute_path)
            except botocore.client.ClientError:
                print(f'Failed to download S3 object with key "{user_friendly_key}". {progress_percent}% complete.')
                traceback.print_exc()
                __delete_empty_file(absolute_path)


def __create_download_folder_path(root: pathlib.Path) -> pathlib.Path:
    """
    Create path to the download directory. This method also ensures that the folder exists
    """
    download_dir = root.joinpath(constants.DOWNLOAD_FOLDER)
    if not download_dir.exists():
        download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def __create_download_file_for_object(absolute_path: pathlib.Path):
    """
    Makes sure the given path exists and opens it for download.
    """
    if not absolute_path.exists():
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.touch()

    return open(absolute_path, 'wb')


def __update_progress(lock: threading.Lock, total_count: int) -> float:
    global download_progress

    with lock:
        download_progress += 1

    return round((download_progress/total_count)*100, 3)


def __delete_empty_file(absolute_path: pathlib.Path):
    """
    Gets rid of leftover files that were not populated due to download errors
    """
    if absolute_path is not None and absolute_path.exists() and absolute_path.stat().st_size == 0:
        absolute_path.unlink()

