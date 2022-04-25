import os
import subprocess

umount_list = filter(None, os.environ.get("AWS_S3_BUCKET_NAMES", "").split(",") + os.environ.get("GCS_BUCKET_NAMES", "").split(","))
for bucket_name in umount_list:
    path_to_umount = f"/home/jovyan/s3-{bucket_name}"
    subprocess.run(
        [
            "umount",
            path_to_umount,
        ]
    )
    subprocess.run(["rmdir", path_to_umount])
