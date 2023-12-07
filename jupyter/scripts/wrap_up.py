import os
import subprocess

if os.environ["OPENHEXA_LEGACY"] == "true":
    # Copy README
    subprocess.run(
        ["cp", "/tmp/notebooks_sample_files/legacy/README.md", "/home/jovyan/README.md"]
    )
else:
    # Copy README (might not be needed, the file is already in the Docker image and we don't have PVC in
    # workspaces)
    subprocess.run(
        ["cp", "/tmp/notebooks_sample_files/README.md", "/home/jovyan/README.md"]
    )

    # Delete work directory if any, and create tmp instead
    subprocess.run(["rmdir", "/home/jovyan/work"])
    subprocess.run(["mkdir", "/home/jovyan/tmp"])

    # Make /home/jovyan read-only
    subprocess.run(["chmod", "a-w", "/home/jovyan"])

    # Make /home/jovyan/worskpace + /home/jovyan/tmp writable
    subprocess.run(["chmod", "g+w", "/home/jovyan/workspace"])
    subprocess.run(["chmod", "g+w", "/home/jovyan/tmp"])
