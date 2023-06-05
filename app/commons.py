from typing import Tuple

import constants


def create_prefix_with_user_id(user_id: str, original_prefix: str) -> tuple[str, str]:
    """
    Creates an S3 prefix with the user ID added to the start. Special case
    'root' is handled differently.
    :return Both the full prefix, and the "internal" start of the prefix. The internal
    part should not be displayed to the user in any way.
    """
    if original_prefix == 'root':
        return f'{user_id}/', f'{user_id}/'
    else:
        return f'{user_id}/{original_prefix}', f'{user_id}/'


def create_restored_prefix_with_user_id(user_id: str, original_prefix: str) -> tuple[str, str]:
    """
    Creates an S3 prefix with 'restored' and the user ID added to the start.
    Special case 'root' is handled differently.
    :return Both the full prefix, and the "internal" start of the prefix. The internal
    part should not be displayed to the user in any way.
    """
    if original_prefix == 'root':
        return f'{constants.RESTORED_PREFIX}{user_id}/', f'{constants.RESTORED_PREFIX}{user_id}/'
    else:
        return f'{constants.RESTORED_PREFIX}{user_id}/{original_prefix}', f'{constants.RESTORED_PREFIX}{user_id}/'


class ObjectsCount:

    def __init__(self, count: int, total_size: int, pages):
        self.count = count
        self.total_size = total_size
        self.pages = pages

    def total_size_in_gb(self) -> float:
        return round(self.total_size / (1024*1024*1024), 3)


def count_objects_with_prefix(s3_client, prefix: str, storage_class: str) -> ObjectsCount:
    """
    Counts how many objects exist with the given prefix and storage class.
    :return: Both the count and the total size in bytes.
    """
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=constants.ARCHIVE_BUCKET_NAME, Prefix=prefix)

    object_count = 0
    objects_total_size = 0
    for page in pages:
        if 'Contents' in page:
            for s3_object in page['Contents']:
                if s3_object['StorageClass'] == storage_class:
                    object_count += 1
                    objects_total_size += s3_object['Size']

    return ObjectsCount(object_count, objects_total_size, pages)
