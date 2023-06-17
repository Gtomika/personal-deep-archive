import multiprocessing

import boto3

import constants
import commons

ARCHIVED = 0
RESTORATION_IN_PROGRESS = 1
RESTORATION_COMPLETE = 2


def process_list_archive_command(aws_session: boto3.Session, user_id: str, command_data: str):
    __process_list_command(aws_session, user_id, command_data, ARCHIVED)


def process_list_restoration_ongoing_command(aws_session: boto3.Session, user_id: str, command_data: str):
    __process_list_command(aws_session, user_id, command_data, RESTORATION_IN_PROGRESS)


def process_list_restored_command(aws_session: boto3.Session, user_id: str, command_data: str):
    __process_list_command(aws_session, user_id, command_data, RESTORATION_COMPLETE)


def __process_list_command(aws_session: boto3.Session, user_id: str, command_data: str, expected_restoration_state: int):
    if command_data != 'root' and not command_data.endswith('/'):
        raise Exception('Prefix must end with / character or be "root"')

    s3_client = aws_session.client('s3', constants.AWS_REGION)
    print(f'Listing your archived contents under "{command_data}", this might take some time...')
    full_prefix, internal_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(
        Bucket=constants.ARCHIVE_BUCKET_NAME,
        Prefix=full_prefix,
        PaginationConfig={
            'PageSize': constants.MAX_PAGE_SIZE
        }
    )

    args = []
    for page in pages:
        args.append((aws_session, full_prefix, expected_restoration_state, page))

    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    results_per_page = thread_pool.starmap(__process_page, args)
    thread_pool.close()
    thread_pool.join()

    results = __aggregate_results(results_per_page)

    if len(results) > 0:
        print(f'Found the following folders and files that match the criteria:')
        for result in results:
            print(result)
    else:
        print('Found nothing under the selected prefix that match the criteria.')


def __aggregate_results(results_per_page):
    aggregated_results = set()
    for result_of_page in results_per_page:
        aggregated_results = aggregated_results.union(result_of_page)
    return aggregated_results


def __process_page(
        aws_session: boto3.Session,
        full_prefix: str,
        expected_restoration_state: str,
        page
):
    s3_client = aws_session.client('s3')
    results = set()
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            head = s3_client.head_object(
                Bucket=constants.ARCHIVE_BUCKET_NAME,
                Key=key
            )
            if expected_restoration_state == __extract_restoration_status(head):
                __process_object(results, full_prefix, key)
    return results


def __process_object(results: set[str], full_prefix: str, full_key: str):
    prefix_of_interest = full_key.removeprefix(full_prefix)

    # is this object in a "folder"?
    if '/' in prefix_of_interest:
        folder = prefix_of_interest.split('/')[0]
        results.add(f'{folder}/')
    else:
        results.add(prefix_of_interest)


def __extract_restoration_status(head) -> int:
    if 'Restore' in head:
        restore_header = head['Restore']
        # the object can be under restoration or the restoration may have completed
        return RESTORATION_IN_PROGRESS if restore_header == 'ongoing-request="true"' else RESTORATION_COMPLETE
    else:
        return ARCHIVED
