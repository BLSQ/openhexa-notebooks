import os
import subprocess
import json
import base64

# TODO: upgrade to more recent version of s3fs, which handles the standard AWS env variables just fine
if os.environ.get("HEXA_FEATURE_FLAG_S3FS", "false") == "true":
    fuse_config = json.loads(base64.b64decode(os.environ["_PRIVATE_FUSE_CONFIG"]))

    os.putenv("AWSACCESSKEYID", fuse_config["access_key_id"])
    os.putenv("AWSSECRETACCESSKEY", fuse_config["secret_access_key"])
    os.putenv("AWSSESSIONTOKEN", fuse_config["session_token"])

    for bucket in fuse_config["buckets"]:
        path_to_mount = os.path.join(f"/home/jovyan/s3-{bucket['name']}")
        region_url = f"https://s3-{bucket['region']}.amazonaws.com/"
        subprocess.run(["echo", "mkdir", "-p", path_to_mount])
        subprocess.run(
            [
                "echo",
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
            ]
        )
