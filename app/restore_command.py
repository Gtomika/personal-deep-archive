import traceback

import boto3
import botocore.client

import constants
import commons


def restore_command(aws_session: boto3.Session, user_id: str, command_data: str):
    """
    After a confirmation, this command triggers the restoration of the DEEP_ARCHIVE objects
    with the given prefix.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: Objects will be restored with this prefix.
    """
    print(f'Checking the objects for restoration with prefix {command_data}...')
    s3_client = aws_session.client('s3')

    s3_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=constants.ARCHIVE_BUCKET_NAME, Prefix=s3_prefix)

    object_count = 0
    objects_total_size = 0
    for page in pages:
        if 'Contents' in page:
            for s3_object in page['Contents']:
                if s3_object['StorageClass'] == 'DEEP_ARCHIVE':
                    object_count += 1
                    objects_total_size += s3_object['Size']

    print(f'A total of {object_count} objects will be restored, with total size of {round(objects_total_size/(1024*1024*1024),3)} GB!')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print('Starting restoration process for selected objects...')
        started_restorations_count = __restore_objects(s3_client, pages, object_count)

        dynamodb_client = aws_session.client('dynamodb')
        __put_restorations_into_notifications_table(dynamodb_client, user_id, started_restorations_count)
        print('Restoration was successfully started. It will take up to 48 hours to complete. You\'ll receive email notification on completion.')
    else:
        print('Aborting restoration...')


def __restore_objects(s3_client, pages, object_count: int) -> int:
    restoration_progress_count = 0
    successfully_started_restorations_count = 0
    for page in pages:
        if 'Contents' in page:
            for s3_object in page['Contents']:
                if s3_object['StorageClass'] == 'DEEP_ARCHIVE':
                    restoration_progress_count += 1
                    try:
                        # objects with prefix 'restored/' are expired in 3 days: bucket lifecycle config
                        s3_client.restore_object(
                            Bucket=constants.ARCHIVE_BUCKET_NAME,
                            Key=s3_object['Key'],
                            RestoreRequest={
                                'Tier': 'Bulk',
                                'OutputLocation': {
                                    'S3': {
                                        'BucketName': constants.ARCHIVE_BUCKET_NAME,
                                        'Prefix': constants.RESTORED_PREFIX,
                                        'StorageClass': 'STANDARD'
                                    }
                                }
                            }
                        )
                        print(f'Restoration started for another object... {round(restoration_progress_count / object_count, 3) * 100}%')
                        successfully_started_restorations_count += 1
                    except botocore.client.ClientError:
                        print(f'Restoration of object {s3_object["Key"]} could not be started!')
                        traceback.print_exc()
    return successfully_started_restorations_count


def __put_restorations_into_notifications_table(dynamodb_client, user_id: str, started_restorations_count: int):
    dynamodb_client.update_item(
        TableName=constants.RESTORATION_NOTIFICATIONS_TABLE_NAME,
        Key={
            'UserId': {
                'S': user_id
            }
        },
        ExpressionAttributeNames={
            '#C': 'OngoingRestorations'
        },
        ExpressionAttributeValues={
            ':c': {
                'N': str(started_restorations_count)  # this overrides existing count! TODO
            }
        },
        UpdateExpression='SET #C = :c'
    )
