import os
from pathlib import Path

# Load main config file
main_config_file_path = Path(__file__).parent / Path("jupyterhub_config_base.py")
load_subconfig(str(main_config_file_path.resolve()))


# Set additional labels on pods (useful for monitoring & billing)
c.KubeSpawner.extra_labels = {"hexa-workspace": "{unescaped_servername}"}
