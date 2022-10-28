<div align="center">
   <img alt="OpenHexa Logo" src="https://raw.githubusercontent.com/BLSQ/openhexa-app/main/hexa/static/img/logo/logo_with_text_grey.svg" height="80">
</div>

OpenHexa Notebooks Component
============================

OpenHexa is an **open-source data integration platform** that allows users to:

- Explore data coming from a variety of sources in a **data catalog**
- Schedule **data pipelines** for extraction & transformation operations
- Perform data analysis in **notebooks**
- Create rich data **visualizations**

<div align="center">
   <img alt="OpenHexa Screenshot" src="https://test.openhexa.org/img/screenshot_catalog.png" hspace="10" height="150">
   <img alt="OpenHexa Screenshot" src="https://test.openhexa.org/img/screenshot_notebook.png" hspace="10" height="150">
</div>

OpenHexa architecture
---------------------

The OpenHexa platform is composed of **three main components**:

- The **App component**, a Django application that acts as the user-facing part of the OpenHexa platform
- The **Notebooks component** (a [JupyterHub](https://jupyter.org/hub) setup)
- The **Data Pipelines component** (build on top of [Airflow](https://airflow.apache.org/))

This repository contains the code for the **Notebooks component**, which provides a Jupyterhub environment destined to 
be embedded within the [OpenHexa App component](https://github.com/blsq/openhexa-app).

The code related to the App component can be found in the
[`openhexa-app`](https://github.com/blsq/openhexa-app) repository, while the Data Pipelines component code resides in
the [`openhexa-pipelines`](https://github.com/blsq/openhexa-pipelines) repository.

Notebooks component overview
----------------------------

The **Notebooks component** is not meant to be use in a stand-alone fashion. It is a part of the OpenHexa platform, and
from a user perspective, it is embedded within the [OpenHexa App](https://github.com/BLSQ/openhexa-app) component.

The **Notebooks component** is a JupyterHub setup, deployed in a **Kubernetes cluster**. OpenHexa relies on the official
[Zero to JupyterHub](https://zero-to-jupyterhub.readthedocs.io/) Jupyterhub distribution, which contains a Helm chart
to manage deployments.

When the hub starts a single-user Jupyter notebook server, it actually spawns a new pod within the Kubernetes cluster. 
Each single-user server instance is totally isolated from other instances.

Those single-user server instances use a customized Docker image based on the `datascience-notebook` image provided by
the [Jupyter Docker Stacks](https://github.com/jupyter/docker-stacks) project. The OpenHexa Docker image is publicly 
available on [Docker Hub](https://hub.docker.com/r/blsq/openhexa-jupyuter).

Authentication
--------------

The **Notebooks component** uses a custom authenticator that will connect to the 
(**App component**)[https://github.com/blsq/openhexa-app] to authenticate users. You will need to have the App 
component up-and-running to be able to authenticate users.

Building the Docker image
-------------------------

The OpenHexa Notebooks base Docker image is publicly available on Docker Hub
([blsq/openhexa-base-notebook](https://hub.docker.com/r/blsq/openhexa-base-notebook)).

This repository also provides a Github workflow to build the Docker image in the `.github/workflows` directory.

To build and push the image manually:

```bash
docker build -t blsq/openhexa-base-notebook:<version> -t blsq/openhexa-base-notebook:latest jupyter
docker push blsq/openhexa-base-notebook:<version>
docker push blsq/openhexa-base-notebook:latest
```

Local development
-----------------

This repository provides a ready-to-use `docker-compose.yaml` file for local development. It assumes that the 
[App component](https://github.com/blsq/openhexa-app) is running on [http://localhost:8000](http://localhost:8000).

Build the images, and you are ready to go:

```bash
docker-compose build
docker-compose up
```