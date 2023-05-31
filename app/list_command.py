import boto3
import pathlib

import constants
import commons


def process_list_archive_command(aws_session: boto3.Session, user_id: str, command_data: str):
    """
    Print all objects that are in the 'DEEP ARCHIVE' storage class. Objects will be aggregated
    into "folders" based on prefix.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: The path to list. Must end with '/' character or be 'root'
    """
    __process_list_command(aws_session, user_id, command_data, 'DEEP_ARCHIVE')


def process_list_restored_command(aws_session: boto3.Session, user_id: str, command_data: str):
    """
    Print all objects that are in the 'STANDARD' (restored) storage class. Objects will be aggregated
    into "folders" based on prefix.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: The path to list. Must end with '/' character or be 'root'
    """
    __process_list_command(aws_session, user_id, command_data, 'STANDARD')


def __process_list_command(aws_session: boto3.Session, user_id: str, command_data: str, storage_class: str):
    if command_data != 'root' and not command_data.endswith('/'):
        raise Exception('Prefix must end with / character or be "root"')

    s3_client = aws_session.client('s3', constants.AWS_REGION)
    print(f'Listing your archived contents under "{command_data}"...')

    list_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    paginator = s3_client.get_paginator('list_objects_v2')
    # print(f'Using the full prefix {list_prefix}')
    pages = paginator.paginate(Bucket=constants.ARCHIVE_BUCKET_NAME, Prefix=list_prefix)

    results = set()
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['StorageClass'] == storage_class:
                    process_object(results, list_prefix, obj)

    if len(results) > 0:
        print(f'Found the following {storage_class} type folders and files:\n')
        for result in results:
            print(result)
    else:
        print('Found nothing under the selected prefix\n')


def process_object(results: set[str], list_prefix: str, object):
    full_key: str = object['Key']
    prefix_of_interest = full_key.removeprefix(list_prefix)

    # is this object in a "folder"?
    if '/' in prefix_of_interest:
        folder = prefix_of_interest.split('/')[0]
        results.add(f'{folder}/')
    else:
        results.add(prefix_of_interest)
