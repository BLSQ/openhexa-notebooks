import os

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
}

# Fix for https://github.com/BLSQ/habari/issues/31
c.GenericFileCheckpoints.root_dir = "./.checkpoints"

c.ServerApp.tornado_settings = {"autoreload": True}

# https://github.com/jupyter-server/jupyter-resource-usage
c.ResourceUseDisplay.track_cpu_percent = True
