import constants


def help_command(email: str):
    print(f'Welcome to your personal deep archive, {email}! You can now start to issue commands.')
    print(f'Source code and documentation {constants.SOURCE_DOCS_URL}')
    print('Your files in the archive are stored deep in the AWS cloud! To download them, they must first be restored. '
          'Restoring has a cost associated, so it must be done sparsely: this is not a file viewer application.')
