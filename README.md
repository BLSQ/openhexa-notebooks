<div align="center">
   <img alt="OpenHEXA Logo" src="https://raw.githubusercontent.com/BLSQ/openhexa-app/main/backend/hexa/static/img/logo/logo_with_text_black.svg" height="80">
</div>
<p align="center">
    <em>Open-source Data integration platform</em>
</p>

# OpenHEXA Notebooks Component

OpenHEXA is an open-source data integration platform developed by [Bluesquare](https://bluesquarehub.com).

Its goal is to facilitate data integration and analysis workflows, in particular in the context of public health
projects.

Please refer to the [OpenHEXA wiki](https://github.com/BLSQ/openhexa/wiki/Home) for more information about OpenHEXA.

The **Notebooks component** is not meant to be use in a stand-alone fashion. It is a part of the OpenHEXA platform, and
from a user perspective, it is embedded within the [OpenHEXA App](https://github.com/BLSQ/openhexa-app) component.

The **Notebooks component** is a JupyterHub setup, deployed in a **Kubernetes cluster**. OpenHEXA relies on the official
[Zero to JupyterHub](https://zero-to-jupyterhub.readthedocs.io/) Jupyterhub distribution, which contains a Helm chart
to manage deployments.

When the hub starts a single-user Jupyter notebook server, it actually spawns a new pod within the Kubernetes cluster.
Each single-user server instance is totally isolated from other instances.

Those single-user server instances use [customized Docker images](https://github.com/BLSQ/openhexa-docker-images)
based on the `datascience-notebook` image provided by the
[Jupyter Docker Stacks](https://github.com/jupyter/docker-stacks) project.

## Docker image

The OpenHEXA customized JupyterHub setup us published as a Docker image on Docker Hub:
[blsq/openhexa-jupyterhub](https://hub.docker.com/r/blsq/openhexa-jupyterhub)

If you're looking something working out of the box for local development, see "Local development" section below.

## Authentication

The **Notebooks component** uses a custom authenticator that will connect to the
[App component](https://github.com/blsq/openhexa-app) to authenticate users. You will need to have the App
component up-and-running to be able to authenticate users.

## Local development

The [Installation instructions](https://github.com/BLSQ/openhexa/wiki/Installation-instructions#development-installation)
section of our wiki gives an overview of the local development setup required to run OpenHEXA locally.

To run the OpenHEXA notebooks components locally, you will need [Docker](https://www.docker.com/).

This repository provides a ready-to-use `docker-compose.yaml` file for local development. It assumes that the
[App component](https://github.com/blsq/openhexa-app) is running on [http://localhost:8000](http://localhost:8000).

If you want to use our published Docker Image of the Jupyter notebook, you can
start JupyterHub as it follows:

```bash
docker compose -f docker-compose.yml -f docker-compose-withdockerhub.yml up
```

Otherwise, build the images (it can take a long time) and you are ready to go:

```bash
docker compose build
docker compose up
```

## Building the Docker image

The custom Jupyterhub is built using a Github workflow (see `.github/workflows` directory).
