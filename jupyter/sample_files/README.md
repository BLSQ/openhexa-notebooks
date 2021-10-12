<div align="center" style="margin-top:20px;">
   <img alt="OpenHexa Logo" src="https://raw.githubusercontent.com/BLSQ/openhexa-app/main/hexa/static/img/logo/logo_with_text_grey.svg" height="80">
</div>

# Welcome to OpenHexa!

Welcome to OpenHexa, the Bluesquare Data Science platform.

This file is an introduction to the platform - make sure you read it before going further as it contains important 
information regarding security.

## 🚧 OpenHexa is alpha/beta software

This platform is a work in progress, and cannot be considered stable yet. Be prepared for some major changes 
along the way.

**Make sure to read the following sections**, as they contain important information about how to use (and not to use) 
the platform.

## 🚒 An important note about sensitive data

At this stage, the OpenHexa platform is not equipped to deal with sensitive data (for example data that contains 
personal information).

**Never upload sensitive or personal data on the OpenHexa platform.**

## 💽 File storage

OpenHexa allows you to store files in 2 different types of storage:

1. **Cloud Storage**: buckets shared with your team
1. A **personal filesystem**: for your personal drafts and temporary data

### Cloud Storage

In the file explorer on the left, you will see one or more directories beginning with `s3:` or `:gcs`.

These directories correspond to Amazon S3 or Google Cloud Storage buckets. They are shared with your team and are 
backed up on a regular basis.  If you experience any problem related to bucket access, please restart the
Jupyter Server, by going to File -> Logout, then clicking on "restart", then "start the server".

**Using Cloud Storage is the recommended way to store code or data in OpenHexa.**

**Pro tip**: you can copy the path to an existing file in this bucket by right-clicking on it and selecting the 
"Copy path" menu item. 

Don't forget to add a **double slash** after the `s3:` prefix at the beginning of the file (this feature will be improved 
in the future so that the copied path can be used right away).

To access the buckets, Jupyter use an authentication system at the start of session. If the credentials change, or if
you receive new credentials or permissions, you need to refresh the authentication by restarting the session. You
can do so by going to File -> Logout, then clicking on "restart", then "start the server".

### Personal filesystem

Any file or folder that you create outside the `s3:` or `gcs:` directories mentioned above are stored in a personal 
filesystem. This filesystem is not shared with your team.

As this filesystem is faster than the S3/GCS buckets, it can be useful for your work in progress.

🚨 **This data is not backed up** and even worse - this filesystem is recreated from time to time, meaning 
that **it should exclusively be used for temporary data and drafts**. We intend to make this personal filesystem 
more resilient in the future, but in the meantime, you need to move "serious" work in Cloud Storage.

## 🚓 An important note about credentials

In the course of your work on the platform, you might need access to specific APIs and databases. Those external 
resources often require credentials.

**Never store those credentials in any form on the platform**.

First, consider whether the data that you want to access can be extracted in a dedicated, secure data pipeline 
outside OpenHexa.

If it is not the case, and you really need to access a protected external resource, use a password prompt so 
that credentials are not leaked in the file itself or in the notebook output.

You can use [getpass](https://docs.python.org/3/library/getpass.html) in Python or its 
sister [getPass](https://github.com/wrathematics/getPass) library in R.

Avoid printing the credentials, as they would be stored in the notebook output.

Once you are satisfied with such an extraction process, especially if it is a recurring task, please 
consider moving it to an external data pipeline.
