import multiprocessing
import time

import boto3

import constants
import commons


def process_list_archive_command(aws_session: boto3.Session, user_id: str, command_data: str):
    with commons.catch_time() as list_timer:
        __process_list_command(aws_session, user_id, command_data)
    print(f'Listing finished at {time.ctime()} and took {list_timer():.4f} seconds')


def __process_list_command(aws_session: boto3.Session, user_id: str, command_data: str):
    if command_data != 'root' and not command_data.endswith('/'):
        raise Exception('Prefix must end with / character or be "root"')

    s3_client = commons.build_s3_client(aws_session)
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
        args.append((full_prefix, page))

    thread_pool = multiprocessing.pool.ThreadPool(processes=constants.THREADS)
    results_per_page = thread_pool.starmap(__process_page, args)
    thread_pool.close()
    thread_pool.join()

    results = __aggregate_results(results_per_page)

    if len(results) > 0:
        print(f'Found the following folders and files under this folder:\n')
        for result in results:
            print(result)
        print('\nPlease note that these may be archived, restored or under restoration right now.')
    else:
        print('Found nothing under the selected prefix in your archive. Try with "list_archive root" to see your folders.')


def __aggregate_results(results_per_page):
    aggregated_results = set()
    for result_of_page in results_per_page:
        aggregated_results = aggregated_results.union(result_of_page)
    return aggregated_results


def __process_page(full_prefix: str, page):
    results = set()
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
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


