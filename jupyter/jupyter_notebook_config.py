import os
import re

from notebook.services.contents.largefilemanager import LargeFileManager
from hybridcontents import HybridContentsManager
from s3contents import S3ContentsManager
from s3contents import GCSContentsManager

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {
        "Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]
    }
}

# Contents managers
# We start with a LargeFileManager at the root, and we will mount other managers depending on
# user permissions
c.NotebookApp.contents_manager_class = HybridContentsManager
c.HybridContentsManager.manager_classes = {
    "": LargeFileManager,
}
c.HybridContentsManager.manager_kwargs = {
    "": {},
}
# S3 managers
# We are looking for bucket names in env variables
s3_bucket_matches = [re.match(r"^S3_([A-Z0-9_]+)_BUCKET_NAME$", k) for k in os.environ]
s3_bucket_keys = [m.group(1) for m in s3_bucket_matches if m is not None]
for s3_bucket_key in s3_bucket_keys:
    try:
        bucket = os.environ[f"S3_{s3_bucket_key}_BUCKET_NAME"]
        access_key_id = os.environ[f"S3_{s3_bucket_key}_ACCESS_KEY_ID"]
        secret_access_key = os.environ[f"S3_{s3_bucket_key}_SECRET_ACCESS_KEY"]
        session_token = os.environ.get(f"S3_{s3_bucket_key}_SESSION_TOKEN")
    except KeyError:
        continue

    bucket_key = f"s3:{bucket}"
    c.HybridContentsManager.manager_classes[bucket_key] = S3ContentsManager
    c.HybridContentsManager.manager_kwargs[bucket_key] = {
        "bucket": bucket,
        "access_key_id": access_key_id,
        "secret_access_key": secret_access_key,
        "session_token": session_token,
    }

# GCS managers
for gcs_config in []:
    bucket_name = gcs_config["bucket_name"]
    bucket_key = f"gcs:{bucket_name}"
    c.HybridContentsManager.manager_classes[bucket_key] = GCSContentsManager
    c.HybridContentsManager.manager_kwargs[bucket_key] = {
        "project": gcs_config["project"],
        "token": gcs_config["token"],
        "bucket": bucket_name,
    }

# Fix for https://github.com/BLSQ/habari/issues/31
c.GenericFileCheckpoints.root_dir = "./.checkpoints"

c.ServerApp.tornado_settings = {"autoreload": True}
