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

    full_prefix, internal_prefix = commons.create_prefix_with_user_id(user_id, command_data)

    object_count = commons.count_objects_with_prefix(s3_client, full_prefix, 'DEEP_ARCHIVE')

    print(f'A total of {object_count.count} objects will be restored, with total size of {object_count.total_size_in_gb()} GB!')
    proceed = input('Are you sure you want to proceed? (Y) ')

    if proceed == 'Y':
        print('Starting restoration process for selected objects...')
        started_restorations_count = __restore_objects(s3_client, object_count.pages, object_count.count)
        print(f'Restoration was successfully started for {started_restorations_count}/{object_count.count} objects.'
              f' It will take up to 48 hours to complete. Check back later.')
    else:
        print('Aborting restoration...')


def __restore_objects(s3_client, pages, object_count: int) -> int:
    restoration_progress_count = 0
    successfully_started_restorations_count = 0
    for page in pages:
        if 'Contents' in page:
            for s3_object in page['Contents']:
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

