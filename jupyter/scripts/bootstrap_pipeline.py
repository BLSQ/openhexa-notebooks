#!/usr/bin/env python
import argparse
import base64
import json
import os
import sys

import requests
from openhexa.sdk.pipelines import download_pipeline, import_pipeline


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def configure_cloud_run():
    # cloud run -> need to download the code from cloud
    if "HEXA_TOKEN" not in os.environ or "HEXA_SERVER_URL" not in os.environ:
        eprint("Need token and url to download the code")
        sys.exit(1)

    access_token = os.environ["HEXA_TOKEN"]
    server_url = os.environ["HEXA_SERVER_URL"]
    run_id = os.environ["HEXA_RUN_ID"]
    workspace_slug = os.environ["HEXA_WORKSPACE"]

    print("Downloading pipeline...")
    os.mkdir("pipeline")
    download_pipeline(
        server_url,
        access_token,
        run_id,
        "pipeline",
    )
    print("Pipeline downloaded.")

    print("Injecting credentials...")
    r = requests.post(
        f"{server_url}/workspaces/credentials/",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"workspace": workspace_slug},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    os.environ.update(data["env"])
    print("Credentials injected.")


def run_pipeline(config):
    if not os.path.exists("pipeline/pipeline.py"):
        eprint("No pipeline.py found")
        sys.exit(1)

    if os.path.exists("./pipeline/requirements.txt"):
        print("Installing requirements...")
        os.system("pip install -r ./pipeline/requirements.txt")

    print("Running pipeline...")
    pipeline = import_pipeline("pipeline")

    pipeline(config=config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["cloudrun", "run"])
    parser.add_argument(
        "--config", default=None, help="Pipeline configuration base64 encoded"
    )
    args = parser.parse_args()

    config = {}
    if args.config:
        config = json.loads(base64.b64decode(args.config).decode("utf-8"))

    if args.command == "cloudrun":
        configure_cloud_run()

    if args.command in ("cloudrun", "run"):
        run_pipeline(config)
    else:
        parser.print_help()
        sys.exit(1)
