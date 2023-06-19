## Archive app

Archiving program that uses AWS S3 glacier to safely store personal data with lower cost then alternatives 
on the market (such as Dropbox).

### Access

Authorization and authentication is done with AWS Cognito. Only I can add new users 
who can use the application, it isn't public.

### Usage

When the program is launched it will log in the user (obtain temporary AWS credentials).
Then, it will ask for the root folder of the data (an absolute path). Then, it can be used with relative paths.
Available commands:

- `list_archive [path]`: List all objects (files) that are in the deep archive starting with the given path prefix.
- `list_ongoing_restoration [path]`: List all objects that are currently being restored.
- `list_restored [path]`: List all objects (files) that are restored and have the given path prefix.
- `archive_data [path]`: Archive files that are under the path on your local machine.
- `restore_data [path]`: Start restoration of files (objects) starting with the given path prefix. Restored 
objects are kept for 10 days, after that they go back to the archive.
- `download_data [path]`: Download **restored** files (objects) starting with the given path prefix. Downloaded 
data will go under `[selected root]/downloads`, keeping the same folder structure as originally.

Deleting data is not supported to achieve maximum safety. It can be done only as admin, manually.

Restoration of Glacier `DEEP_ARCHIVE` data can take up to 48 hours. Users are 
subscribed to an AWS SNS topic that sends an email notification when their download 
is complete.

### Example workflows

Before each usage:

- Run `main.py`, enter credentials and the root folder of the data. For example the root folder may be 
`C:/archive`. It must be an existing directory.

#### To archive data

- Make sure to put any files that should be archived under the selected root. The folder structure will be 
maintained inside the archive.
- `archive_data root` can be used to archive everything in that folder. To limit the operation to some other folder,
the `archive_data holiday_images/` can be used which will, in this case, only archive files under `C:/archive/holiday_images`
- The archived data can be listed with `list_archive root` or `list_archive holiday_images/`.

#### To restore and download data

For example, we want to restore the holiday images folder from the archive, because the originals were lost.

- Use `restore_data holiday_images/` to start restoration: it will take up to 48 hours.
- Check back later and use `list_ongoing_restoration holiday_images/` or `list_restored holiday_images/` to see if
all files are restored, or not yet.
- Once all files are restored, download them with `download_data holiday_images/`. The files will be placed under your 
root, in this case `C:/archive/holiday_images`.

### Costs

S3 `DEEP_ARCHIVE` storage class is extremely cheap, but there are restoration and 
upload/download costs included too. Other AWS services such as Cognito or SNS fall 
into the free tier.

### Development data

To speed up testing the `credentials.json` and `paths.json` can be placed into the 
same folder where `main.py` is. If this data is found, there will be no command line 
prompt for credentials and the root folder.