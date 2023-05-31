

def create_prefix_with_user_id(user_id: str, original_prefix: str):
    """
    Creates an S3 prefix with the user ID added to the start. Special case
    'root' is handled differently.
    """
    if original_prefix == 'root':
        return f'{user_id}/'
    else:
        return f'{user_id}/{original_prefix}'
