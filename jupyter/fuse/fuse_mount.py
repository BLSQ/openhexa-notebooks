import os
import subprocess
import json
import base64

aws_fuse_config = json.loads(base64.b64decode(os.environ["AWS_S3_FUSE_CONFIG"]))
os.putenv("AWSACCESSKEYID", aws_fuse_config["AWS_ACCESS_KEY_ID"])
os.putenv("AWSSECRETACCESSKEY", aws_fuse_config["AWS_SECRET_ACCESS_KEY"])
os.putenv("AWSSESSIONTOKEN", aws_fuse_config["AWS_SESSION_TOKEN"])

for bucket in filter(None, aws_fuse_config["buckets"]):
    path_to_mount = f"/home/jovyan/s3-{bucket['name']}"
    region_url = f"https://s3-{bucket['region']}.amazonaws.com/"
    subprocess.run(["mkdir", "-p", path_to_mount])
    subprocess.run(
        [
            "s3fs",
            bucket["name"],
            path_to_mount,
            "-o",
            "allow_other",
            "-o",
            "url=" + region_url,
            # Debug
            # "-o",
            # "dbglevel=info",
            # "-f",
            # "-o",
            # "curldbg",
        ] + (["-o", "ro"] if bucket["mode"] == "RO" else [])
    )

gcsfuse_credentials_file = f"/home/jovyan/.gcsfuse.json"
os.putenv("GOOGLE_APPLICATION_CREDENTIALS", gcsfuse_credentials_file)
with open(gcsfuse_credentials_file, "w") as fd:
    fd.write( base64.b64decode(os.environ.get("GCS_CREDENTIALS", "").encode()).decode() );

gcsfuse_buckets = json.loads(base64.b64decode(os.environ["GCS_BUCKETS"]))
for bucket in filter(None, gcsfuse_buckets["buckets"]):
    path_to_mount = f"/home/jovyan/gcs-{bucket['name']}"
    subprocess.run(["mkdir", "-p", path_to_mount])
    subprocess.run(
        [
            "gcsfuse",
            bucket["name"],
            path_to_mount,
        ] + (["-o", "ro"] if bucket["mode"] == "RO" else [])
    )
