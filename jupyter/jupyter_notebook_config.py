import os

from notebook.services.contents.largefilemanager import LargeFileManager
from hybridcontents import HybridContentsManager
from s3contents import S3ContentsManager

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
}

# Contents managers
if os.environ.get("HEXA_FEATURE_FLAG_S3FS", "false") == "false":
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
    s3_bucket_names = filter(None, os.environ.get("AWS_S3_BUCKET_NAMES", "").split(","))
    for s3_bucket_name in s3_bucket_names:
        bucket_key = f"s3:{s3_bucket_name}"
        c.HybridContentsManager.manager_classes[bucket_key] = S3ContentsManager
        c.HybridContentsManager.manager_kwargs[bucket_key] = {
            "bucket": s3_bucket_name,
        }

    # Fix for https://github.com/BLSQ/habari/issues/31
    c.GenericFileCheckpoints.root_dir = "./.checkpoints"

c.ServerApp.tornado_settings = {"autoreload": True}

# https://github.com/jupyter-server/jupyter-resource-usage
c.ResourceUseDisplay.track_cpu_percent = True
