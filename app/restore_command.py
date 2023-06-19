import multiprocessing.pool
import threading
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
    s3_client = aws_session.client('s3')

    full_prefix, internal_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    object_count = commons.count_objects_with_prefix(s3_client, full_prefix)

    print(f'A total of {object_count.count} objects will be restored, with total size of {object_count.total_size_in_gb()} GB!')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print(f'Starting restoration process for selected objects using {constants.THREADS} parallel processes...')
        started_restorations_count = __restore_objects(aws_session, object_count.pages, object_count.count)
        print(f'Restoration was successfully started for {started_restorations_count}/{object_count.count} objects.'
              f' It will take up to 48 hours to complete. Check back later.')
    else:
        print('Aborting restoration...')


restoration_progress_count = 0
successfully_started_restorations_count = 0


def __restore_objects(aws_session: boto3.Session, pages, object_count: int) -> int:
    global restoration_progress_count, successfully_started_restorations_count

    restoration_progress_count = 0
    successfully_started_restorations_count = 0

    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    lock = threading.Lock()

    for page in pages:
        thread_pool.apply_async(__restore_objects_page, (aws_session, page, lock, object_count))

    thread_pool.close()
    thread_pool.join()

    return successfully_started_restorations_count


def __restore_objects_page(aws_session: boto3.Session, page, lock: threading.Lock, object_count: int):
    global restoration_progress_count, successfully_started_restorations_count

    s3_client = aws_session.client('s3')
    if 'Contents' in page:
        for s3_object in page['Contents']:
            progress_percent = __update_progress(lock, object_count)
            try:
                # objects with prefix 'restored/' are expired in 3 days: bucket lifecycle config
                s3_client.restore_object(
                    Bucket=constants.ARCHIVE_BUCKET_NAME,
                    Key=s3_object['Key'],
                    RestoreRequest={
                        'GlacierJobParameters': {
                            'Tier': 'Bulk',
                        },
                        'Days': 10
                    }
                )
                print(f'Restoration started for another object... {progress_percent}% complete')
                with lock:
                    successfully_started_restorations_count += 1
            except botocore.client.ClientError:
                print(f'Restoration of object {s3_object["Key"]} could not be started! {progress_percent}% complete')
                traceback.print_exc()


def __update_progress(lock: threading.Lock, total_count: int) -> float:
    global restoration_progress_count

    with lock:
        restoration_progress_count += 1

    return round((restoration_progress_count/total_count)*100, 3)
