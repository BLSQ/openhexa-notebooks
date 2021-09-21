import os
import subprocess

if os.environ.get("HEXA_FEATURE_FLAG_S3FS", "false") == "true":
    for bucket_name in os.environ.get("AWS_S3_BUCKET_NAMES", "").split(","):
        path_to_umount = os.path.join(f"/home/jovyan/s3-{bucket_name}")
        subprocess.run(
            [
                "umount",
                path_to_umount,
            ]
        )
        subprocess.run(["rmdir", path_to_umount])
