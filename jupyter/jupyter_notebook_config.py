import os
import re

from notebook.services.contents.largefilemanager import LargeFileManager
from hybridcontents import HybridContentsManager
from s3contents import S3ContentsManager
from s3contents import GCSContentsManager

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
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
s3_bucket_names = os.environ.get("AWS_S3_BUCKET_NAMES", "").split(",")
for s3_bucket_name in s3_bucket_names:
    bucket_key = f"s3:{s3_bucket_name}"
    c.HybridContentsManager.manager_classes[bucket_key] = S3ContentsManager
    c.HybridContentsManager.manager_kwargs[bucket_key] = {
        "bucket": s3_bucket_name,
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
