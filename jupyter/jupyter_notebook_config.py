import os

from notebook.services.contents.largefilemanager import LargeFileManager
from hybridcontents import HybridContentsManager

c = get_config()

# Iframe stuff
c.NotebookApp.tornado_settings = {
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
}

# Contents managers
# We start with a LargeFileManager at the root, and we will mount other managers depending on
# user permissions
c.NotebookApp.contents_manager_class = HybridContentsManager
c.HybridContentsManager.manager_classes = {
    "": LargeFileManager,
}
c.HybridContentsManager.manager_kwargs = {
    "": {},
}

# Fix for https://github.com/BLSQ/habari/issues/31
c.GenericFileCheckpoints.root_dir = "./.checkpoints"

c.ServerApp.tornado_settings = {"autoreload": True}

# https://github.com/jupyter-server/jupyter-resource-usage
c.ResourceUseDisplay.track_cpu_percent = True
