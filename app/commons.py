import pathlib

import constants


class FilesData:

    def __init__(self):
        self.file_count = 0
        self.total_size = 0
        self.files = list()

    def register_file(self, file_size: int, file_path_absolute: str, file_path_relative: str):
        self.file_count += 1
        self.total_size += file_size
        self.files.append({
            'path_relative': file_path_relative,
            'path_absolute': file_path_absolute
        })

    def total_size_gb(self) -> float:
        return self.total_size/(1024*1024*1024)


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


def extract_command_arguments(command: str) -> str:
    return command.split(sep=' ')[1]


def validate_root_folder(root: pathlib.Path):
    if not root.exists() or not root.is_dir():
        raise 'Root of the archive must be an existing folder!'


def get_files_data(root: pathlib.Path, absolute_path: pathlib.Path) -> FilesData:
    """
    Gather stats about the affected files.
    """
    if not absolute_path.exists() or not absolute_path.is_dir():
        raise 'Path specified must point to an existing directory'

    data = FilesData()
    for file in pathlib.Path(absolute_path).rglob('*.*'):
        if file.is_file():
            absolute_path_string = file.as_posix()
            relative_path_string = file.relative_to(root).as_posix()
            # print(f'Found file: {absolute_path_string} ({relative_path_string})')
            data.register_file(file.stat().st_size, absolute_path_string, relative_path_string)
    return data