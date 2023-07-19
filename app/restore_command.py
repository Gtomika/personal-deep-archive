import multiprocessing.pool
import threading
import time
import traceback

import boto3
import botocore.client

import constants
import commons


def process_restore_command(aws_session: boto3.Session, user_id: str, command_data: str):
    """
    After a confirmation, this command triggers the restoration of the DEEP_ARCHIVE objects
    with the given prefix.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: Objects will be restored with this prefix.
    """
    print(f'Checking the objects for restoration with prefix {command_data}...')
    s3_client = commons.build_s3_client(aws_session)

    full_prefix, internal_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    object_count = commons.count_objects_with_prefix(s3_client, full_prefix)

    print(f'A total of {object_count.count} objects will be restored, with total size of {object_count.total_size_in_gb()} GB!')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print(f'Starting restoration process for selected objects using {constants.THREADS} parallel processes at {time.ctime()}')
        with commons.catch_time() as restore_timer:
            started_restorations_count = __restore_objects(aws_session, object_count.pages, object_count.count, internal_prefix)
        print(f'Restoration was successfully started for {started_restorations_count}/{object_count.count} objects at {time.ctime()}'
              f' and took {restore_timer():.4f} seconds. It will take up to 48 hours to complete restorations. Check back later.')
    else:
        print('Aborting restoration...')


restoration_progress_count = 0
successfully_started_restorations_count = 0


def __restore_objects(
        aws_session: boto3.Session,
        pages,
        object_count: int,
        internal_prefix: str
) -> int:
    global restoration_progress_count, successfully_started_restorations_count

    restoration_progress_count = 0
    successfully_started_restorations_count = 0

    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    lock = threading.Lock()

    for page in pages:
        thread_pool.apply_async(__restore_objects_page, (aws_session, page, lock, object_count, internal_prefix))

    thread_pool.close()
    thread_pool.join()

    return successfully_started_restorations_count


def __restore_objects_page(
        aws_session: boto3.Session,
        page,
        lock: threading.Lock,
        object_count: int,
        internal_prefix: str
):
    global restoration_progress_count, successfully_started_restorations_count

    s3_client = commons.build_s3_client(aws_session)
    if 'Contents' in page:
        for s3_object in page['Contents']:
            key = s3_object['Key']
            user_friendly_key = key.removeprefix(internal_prefix)
            progress_percent = __update_progress(lock, object_count)
            try:
                response = s3_client.restore_object(
                    Bucket=constants.ARCHIVE_BUCKET_NAME,
                    Key=key,
                    RestoreRequest={
                        'GlacierJobParameters': {
                            'Tier': 'Bulk',
                        },
                        'Days': 10
                    }
                )
                status_code = response['ResponseMetadata']['HTTPStatusCode']
                if status_code == 202:
                    print(f'Restoration started for object "{user_friendly_key}"... {progress_percent}% complete')
                    with lock:
                        successfully_started_restorations_count += 1
                else:
                    print(f'The object "{user_friendly_key} is already restored and ready for download... {progress_percent}% complete"')
            except botocore.client.ClientError as e:
                if e.response['Error']['Code'] == 'RestoreAlreadyInProgress':
                    print(f'The object "{user_friendly_key} is currently being restored, please wait for finish... {progress_percent}% complete"')
                else:
                    print(f'Restoration of object "{user_friendly_key}" could not be started: {e.response["Error"]["Code"]}! {progress_percent}% complete')
                    traceback.print_exc()


def __update_progress(lock: threading.Lock, total_count: int) -> float:
    global restoration_progress_count

    with lock:
        restoration_progress_count += 1

    return round((restoration_progress_count/total_count)*100, 3)
