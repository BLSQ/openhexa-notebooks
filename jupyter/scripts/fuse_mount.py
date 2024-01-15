import base64
import http.server
import json
import multiprocessing
import os
import subprocess
import time

# Git plugin / deactivate if no feature flag
# TODO: this has nothing to do with Fuse, this file should be reworked
if not os.environ.get("GIT_EXTENSION_ENABLED", "false") == "true":
    subprocess.run(
        ["/opt/conda/bin/jupyter", "labextension", "disable", "@jupyterlab/git"]
    )

# S3 Fuse
# b64("{}") == b'e30='
aws_fuse_config = json.loads(
    base64.b64decode(os.environ.get("AWS_S3_FUSE_CONFIG", b"e30="))
)

# tldr: dont use putenv https://docs.python.org/2/library/os.html#os.environ
os.environ["AWSACCESSKEYID"] = aws_fuse_config.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWSSECRETACCESSKEY"] = aws_fuse_config.get("AWS_SECRET_ACCESS_KEY", "")
os.environ["AWSSESSIONTOKEN"] = aws_fuse_config.get("AWS_SESSION_TOKEN", "")
aws_endpoint = aws_fuse_config.get("AWS_ENDPOINT", "")
s3_is_minio = True if aws_endpoint else False

for bucket in filter(None, aws_fuse_config.get("buckets", [])):
    path_to_mount = f"/home/jovyan/s3-{bucket['name']}"
    region_url = (
        aws_endpoint
        if aws_endpoint
        else f"https://s3-{bucket['region']}.amazonaws.com/"
    )
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
        ]
        + (["-o", "ro"] if bucket["mode"] == "RO" else [])
        # MinIO doesn't support the subdomain request style, use the older path request style.
        + (["-o", "use_path_request_style"] if s3_is_minio else [])
    )

GCS_TOKEN = os.environ.get("GCS_TOKEN", "")
WORKSPACE_BUCKET_NAME = os.environ.get("WORKSPACE_BUCKET_NAME", "")

# NO GCS_TOKEN but a WORKSPACE BUCKET NAME => minio or s3 for the workspace mount
if not(GCS_TOKEN) and WORKSPACE_BUCKET_NAME:
    path_to_mount = "/home/jovyan/workspace"
    region_url = aws_endpoint
    
    subprocess.run(["mkdir", "-p", path_to_mount])
    results = subprocess.run(
        [
            "s3fs",
            WORKSPACE_BUCKET_NAME,
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
        # always rw  # + (["-o", "ro"] if bucket["mode"] == "RO" else [])
        # MinIO doesn't support the subdomain request style, use the older path request style.
        + (["-o", "use_path_request_style"] if s3_is_minio else [])
    )


# GCS Fuse
# gcsfuse offers 2 choices to authenticate:
# 1) using a 'JSON key file', with static credentials
# 2) using a token (that can be a short lived one) served over HTTP
# So we span an HTTP server to use the second option.
# Yes, it's strange, but unless we want to fork gcsfuse, we will have to live with this


if GCS_TOKEN and WORKSPACE_BUCKET_NAME:

    class serveGCStoken(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes('{ "access_token": "' + GCS_TOKEN + '" }', "utf-8"))

    webServer = http.server.HTTPServer(("127.0.0.1", 4321), serveGCStoken)
    proc = multiprocessing.Process(target=webServer.serve_forever, args=())
    proc.start()
    time.sleep(0.5)

    path_to_mount = "/home/jovyan/workspace"
    subprocess.run(["mkdir", "-p", path_to_mount], check=True)
    args = [
        "gcsfuse",
        "-o",
        "allow_other",
        "--implicit-dirs",  # Also create implicit directories structure (i.e. key /a/b/c/d will create /a, /a/b, /a/b/c)
    ]

    # Use the custom token server to get the token
    args.extend(
        ["--token-url", "http://127.0.0.1:4321/", WORKSPACE_BUCKET_NAME, path_to_mount]
    )
    try:
        subprocess.run(args, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise
    finally:
        proc.terminate()
        time.sleep(0.5)
        proc.close()
