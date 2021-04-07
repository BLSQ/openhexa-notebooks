import os

from notebook.services.contents.largefilemanager import LargeFileManager
from hybridcontents import HybridContentsManager
from s3contents import S3ContentsManager
from s3contents import GCSContentsManager

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {
        "Content-Security-Policy": f"frame-ancestors 'self' {os.environ['APP_URL']}"
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
for s3_bucket_name in os.environ.get("S3_BUCKET_NAMES", "").split(","):
    bucket_key = f"s3:{s3_bucket_name}"
    c.HybridContentsManager.manager_classes[bucket_key] = S3ContentsManager
    c.HybridContentsManager.manager_kwargs[bucket_key] = {
        "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
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
