import os
import subprocess
import json
import base64

# TODO: upgrade to more recent version of s3fs, which handles the standard AWS env variables just fine
os.putenv("AWSACCESSKEYID", os.environ["AWS_ACCESS_KEY_ID"])
os.putenv("AWSSECRETACCESSKEY", os.environ["AWS_SECRET_ACCESS_KEY"])
os.putenv("AWSSESSIONTOKEN", os.environ["AWS_SESSION_TOKEN"])

buckets_ro = os.environ.get("AWS_S3_BUCKET_RO_NAMES", "").split(",")

for bucket_name in filter(None, os.environ.get("AWS_S3_BUCKET_NAMES", "").split(",")):
    path_to_mount = f"/home/jovyan/s3-{bucket_name}"
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
        ] + (["-o", "ro"] if bucket_name in buckets_ro else [])
    )

gcsfuse_config_file = f"/home/jovyan/.gcsfuse.json"
os.putenv("GOOGLE_APPLICATION_CREDENTIALS", gcsfuse_config_file)
with open(gcsfuse_config_file, "w") as fd:
    fd.write( base64.b64decode(os.environ.get("GCS_CREDENTIALS", "").encode()).decode() );

for bucket_name in filter(None, os.environ.get("GCS_BUCKET_NAMES", "").split(",")):
    path_to_mount = f"/home/jovyan/gcs-{bucket_name}"
    subprocess.run(["mkdir", "-p", path_to_mount])
    subprocess.run(
        [
            "gcsfuse",
            bucket_name,
            path_to_mount,
        ]
    )
