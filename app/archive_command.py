import boto3
import pathlib
import unicodedata

import constants

archived_data_price_per_gb = 0.00099


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


def archive_command(root: pathlib.Path, aws_session: boto3.Session, user_id: str, command_data: str):
    """
    Upload all files with the given prefix as glacier 'DEEP_ARCHIVE' objects. Confirmation is
    required: all info about the files will be listed.
    :param root: The root folder path of the archive.
    :param aws_session: AWS session with correct credentials that only allow the users prefix.
    :param user_id: ID of the user used as S3 prefix.
    :param command_data: Files will be archived under this relative path
    """
    if command_data == 'root':
        absolute_path = root
    else:
        absolute_path = root.joinpath(command_data)

    print(f'Files under "{absolute_path.as_posix()} will be archived."')
    print('Checking amount of files...')
    files_data = __get_files_data(root, absolute_path)
    print(f'Found a total of {files_data.file_count} files using {files_data.total_size_gb()} GB of space.')
    print(f'Estimated cost for archiving these files is {round(files_data.total_size_gb() * archived_data_price_per_gb, 5)}$ per month. '
          f'A relatively small one time upload cost will apply.')

    proceed = input('Are you sure you want to proceed with archiving these files? (Y)')
    if proceed == 'Y':
        print('Starting the upload of the selected files...')
        s3_client = aws_session.client('s3')
        __upload_files_to_archive(s3_client, user_id, files_data)
        print(f'Complete! Archived {files_data.file_count} files in your deep archive! Use "list_archive root" to see them.')
    else:
        print('Aborting the archive command...')


def __get_files_data(root: pathlib.Path, absolute_path: pathlib.Path) -> FilesData:
    """
    Gather stats about the affected files.
    """
    data = FilesData()
    for file in pathlib.Path(absolute_path).rglob('*.*'):
        if file.is_file():
            absolute_path_string = file.as_posix()
            relative_path_string = file.relative_to(root).as_posix()
            # print(f'Found file: {absolute_path_string} ({relative_path_string})')
            data.register_file(file.stat().st_size, absolute_path_string, relative_path_string)
    return data


def __upload_files_to_archive(s3_client, user_id: str, data: FilesData):
    progress = 0
    for file in data.files:
        s3_client.upload_file(
            Filename=file['path_absolute'],
            Bucket=constants.ARCHIVE_BUCKET_NAME,
            Key=f'{user_id}/{__sanitize_prefix(file["path_relative"])}',
            ExtraArgs={
                'StorageClass': 'DEEP_ARCHIVE'
            }
        )
        progress += 1
        print(f'Uploaded {progress}/{data.file_count} files to archive... {round((progress/data.file_count)*100, 2)}% complete')


def __sanitize_prefix(prefix: str):
    prefix = prefix.replace(' ', '_')
    prefix = unicodedata.normalize('NFKD', prefix)
    return prefix.encode('ASCII', 'ignore')


# aws_session = boto3.Session()
# user_id = 'test_data'
# archive_command(pathlib.Path('C:\Programozas\Python\personal-deep-archive'), aws_session, user_id, command_data='app/test_data/')
