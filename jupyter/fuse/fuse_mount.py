import os
import subprocess
import json
import base64
import http.server
import multiprocessing
import time

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

# gcsfuse offers 2 choises to authenticate:
# 1) using a 'JSON key file', with static credentials
# 2) using a token (that can be a short lived one) served over HTTP
# So we span an HTTP server to use the second option.
# Yes, it's strange, but unless we want to fork gcsfuse, we will have to live with this
GCS_TOKEN = os.environ.get("GCS_TOKEN", "")

if GCS_TOKEN:
  class serveGCStoken(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes('{ "access_token": "' + GCS_TOKEN + '" }', "utf-8"))

  webServer = http.server.HTTPServer(('127.0.0.1',4321), serveGCStoken)
  x = multiprocessing.Process(target=webServer.serve_forever, args=())
  x.start()
  time.sleep(1)

  # b64("{}") == b'e30='
  gcsfuse_buckets = json.loads(base64.b64decode(os.environ.get("GCS_BUCKETS", b'e30=')))
  for bucket in filter(None, gcsfuse_buckets.get("buckets", [])):
    path_to_mount = f"/home/jovyan/gcs-{bucket['name']}"
    subprocess.run(["mkdir", "-p", path_to_mount])
    subprocess.run(
        [
            "gcsfuse",
            "--token-url",
            "http://127.0.0.1:4321/",
            bucket["name"],
            path_to_mount,
        ] + (["-o", "ro"] if bucket["mode"] == "RO" else [])
    )
  x.terminate()
