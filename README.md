## Archive app

Archiving program that uses AWS S3 glacier to safely story personal data.

### Access

Authorization and authentication is done with AWS Cognito. Only I can add new users 
who can use the application, it isn't public.

### Usage

When the program is launched it will log in the user (obtain temporary AWS credentials).
Then, it will ask for the root folder of the data (an absolute path). Then, it can be used with relative paths.
Available commands:

- `list_archive [path]`: List all objects (files) that are in the deep archive starting with the given path prefix.
- `list_restored [path]`: List all objects (files) that are restored and ready to be downloaded starting with the given path prefix.
- `archive_data [path]`: Archive files that are under the path on your local machine.
- `restore_data [path]`: Start restoration of files (objects) starting with the given path prefix.
- `download_data [path]`: Download **restored** files (objects) starting with the given path prefix.

Deleting data is not supported to achieve maximum safety. It can be done only as admin.

Restoration of Glacier `DEEP_ARCHIVE` data can take up to 48 hours. Users are 
subscribed to an AWS SNS topic that sends an email notification when their download 
is complete.

### Costs

S3 `DEEP_ARCHIVE` storage class is extremely cheap, but there are restoration and 
upload/download costs included too. Other AWS services such as Cognito or SNS fall 
into the free tier.

### Development data

To speed up testing the `credentials.json` and `paths.json` can be placed into the 
same folder where `main.py` is. If this data is found, there will be no command line 
prompt for credentials and the root folder.