import os
import subprocess

# TODO: upgrade to more recent version of s3fs, which handles the standard AWS env variables just fine
if os.environ.get("HEXA_FEATURE_FLAG_S3FS", "false") == "true":
    os.putenv("AWSACCESSKEYID", os.environ["AWS_ACCESS_KEY_ID"])
    os.putenv("AWSSECRETACCESSKEY", os.environ["AWS_SECRET_ACCESS_KEY"])
    os.putenv("AWSSESSIONTOKEN", os.environ["AWS_SESSION_TOKEN"])
    for bucket_name in os.environ.get("AWS_S3_BUCKET_NAMES", "").split(","):
        path_to_mount = os.path.join(f"/home/jovyan/s3-{bucket_name}")
        subprocess.run(["mkdir", "-p", path_to_mount])
        subprocess.run(
            [
                "s3fs",
                bucket_name,
                path_to_mount,
                "-o",
                "allow_other",
                # Debug
                # "-o",
                # "dbglevel=info",
                # "-f",
                # "-o",
                # "curldbg",
            ]
        )