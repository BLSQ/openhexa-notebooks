import os
import subprocess
import json
import base64

umount_list = filter(None, os.environ.get("AWS_S3_BUCKET_NAMES", "").split(","))
for bucket_name in umount_list:
    path_to_umount = f"/home/jovyan/s3-{bucket_name}"
    subprocess.run(
        [
            "umount",
            path_to_umount,
        ]
    )
    subprocess.run(["rmdir", path_to_umount])

# b64("{}") == b'e30='
gcsfuse_buckets = json.loads(base64.b64decode(os.environ.get("GCS_BUCKETS", b"e30=")))
for bucket in filter(None, gcsfuse_buckets.get("buckets", [])):
    mount_point = bucket.get("mount", f"/gcs-{bucket['name']}")
    path_to_umount = "/home/jovyan" + mount_point
    subprocess.run(
        [
            "umount",
            path_to_umount,
        ]
    )
    subprocess.run(["rmdir", path_to_umount])
