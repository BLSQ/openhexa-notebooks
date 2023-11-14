<div align="center">
   <img alt="OpenHexa Logo" src="https://raw.githubusercontent.com/BLSQ/openhexa-app/main/hexa/static/img/logo/logo_with_text_grey.svg" height="80">
</div>
<p align="center">
    <em>Open-source Data integration platform</em>
</p>

OpenHexa Notebooks Component
============================

OpenHexa is an open-source data integration platform developed by [Bluesquare](https://bluesquarehub.com).

Its goal is to facilitate data integration and analysis workflows, in particular in the context of public health
projects.

Please refer to the [OpenHexa wiki](https://github.com/BLSQ/openhexa/wiki/Home) for more information about OpenHexa.

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

For more information about the technical aspects of OpenHexa, you might be interested in the two following wiki pages:

- [Installing OpenHexa](https://github.com/BLSQ/openhexa/wiki/Installation-instructions)
- [Technical Overview](https://github.com/BLSQ/openhexa/wiki/Technical-overview)

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

Container
---------

OpenHexa Notebook and JupyterHub are published as a Docker Image on Docker Hub:
[blsq/openhexa-base-notebook](https://hub.docker.com/r/blsq/openhexa-base-notebook) and
[blsq/openhexa-jupyterhub](https://hub.docker.com/r/blsq/openhexa-base-notebook) (resp.).

If you're looking something working out of the box for local development, go to
the next section.

Local development
-----------------

This repository provides a ready-to-use `docker-compose.yaml` file for local development. It assumes that the 
[App component](https://github.com/blsq/openhexa-app) is running on [http://localhost:8000](http://localhost:8000).

If you want to use our published Docker Image of the Jupyter notebook, you can
start JupyterHub as it follows:

```bash
docker compose -f docker-compose.yml -f docker-compose-withdockerhub.yml up
```

Otherwise, build the images (that can take a long time) and you are ready to go:

```bash
docker compose build
docker compose up
```

### Publishing the pipelines image

The docker image `openhexa-base-notebook` is also used to run pipelines. Follow the steps below to publish a new docker image depending on the environment on which you want to deploy it.

```shell
# For demo environment
docker tag blsq/openhexa-base-notebook:<version> blsq/openhexa-base-notebook:latest
docker push blsq/openhexa-base-notebook:latest
# For production environment
docker tag blsq/openhexa-base-notebook:<version> blsq/openhexa-base-notebook:production
docker push blsq/openhexa-base-notebook:production
```
