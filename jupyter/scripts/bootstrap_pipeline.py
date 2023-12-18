#!/usr/bin/env python
import argparse
import base64
import json
import os
import sys
import subprocess

import requests
from openhexa.sdk.pipelines import download_pipeline, import_pipeline


def run_pipeline(config):
    if not os.path.exists("pipeline/pipeline.py"):
        print("No pipeline.py found", file=sys.stderr)
        sys.exit(1)

    if os.path.exists("./pipeline/requirements.txt"):
        print("Installing requirements...")
        os.system("pip install -r ./pipeline/requirements.txt")

    installed, uninstalled = version_info()
    if len(installed) > 0:
        print("Using {}".format(", ".join(installed)))
    if len(uninstalled) > 0:
        print("Warning, uninstalled libraries: {}".format(", ".join(uninstalled)))

    print("Running pipeline...")
    pipeline = import_pipeline("pipeline")
    pipeline(config=config)


def configure_cloud_run():
    # cloud run -> need to download the code from cloud
    if "HEXA_TOKEN" not in os.environ or "HEXA_SERVER_URL" not in os.environ:
        print("Need token and url to download the code", file=sys.stderr)
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

    print("Mounting buckets...")
    # setup fuse for buckets
    if os.path.exists("/home/jovyan/.hexa_scripts/fuse_mount.py"):
        # import fuse mount script _after_ env variables injection
        sys.path.insert(1, "/home/jovyan/.hexa_scripts")
        import fuse_mount  # noqa: F401, E402

    if os.path.exists("/home/jovyan/.hexa_scripts/wrap_up.py"):
        # setup sample files, et co...
        os.environ["OPENHEXA_LEGACY"] = "false"


def version_info():
    installed = []
    uninstalled = []
    for lib in ["openhexa.sdk", "openhexa.toolbox"]:
        completed_process = subprocess.run(f"pip freeze | grep {lib}", shell=True, capture_output=True)
        lib_version = completed_process.stdout.decode("utf-8").strip()
        if lib_version == "":
            uninstalled.append(lib)
        else:
            installed.append(lib_version)

    return installed, uninstalled


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["cloudrun", "run"])
    parser.add_argument(
        "--config", default=None, help="Pipeline configuration base64 encoded"
    )
    args = parser.parse_args()

    if args.command == "cloudrun":
        configure_cloud_run()

    if args.command in ("cloudrun", "run"):
        args_config = json.loads(base64.b64decode(args.config).decode("utf-8")) if args.config else {}
        run_pipeline(args_config)
        if args.command == "cloudrun" and os.path.exists(
                "/home/jovyan/.hexa_scripts/fuse_umount.py"
        ):
            # clean up fuse & umount at the end
            import fuse_umount  # noqa: F401, E402
    else:
        parser.print_help()
        sys.exit(1)
