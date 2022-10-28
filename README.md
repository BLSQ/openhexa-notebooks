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

Provisioning
------------

**Note:** the following instructions are tailored to a Google Cloud Platform setup (using Google Kubernetes Engine and
Google Cloud SQL). OpenHexa can be deployed on other cloud providers or in a private cloud, but you will need to adapt
the instructions below to your infrastructure of choice.

### Requirements

In order to run the OpenHexa **App component**, you will need:

1. A **Kubernetes cluster**
1. A **PostgreSQL server** running PostgreSQL 11 or later
1. An up-and-running instance of the OpenHexa **App component** (see 
   [https://github.com/blsq/openhexa-app](https://github.com/blsq/openhexa-app))

It is perfectly fine to run the OpenHexa **Notebooks component** in an existing Kubernetes cluster. All the Kubernetes
resources created for this component will be attached to a specific Kubernetes namespace named `hexa-notebooks`.

### Configure gcloud

We will need the [`gcloud`](https://cloud.google.com/sdk/gcloud) command-line tool for the next steps. Make sure it is
installed and configured properly - among other things, that the appropriate configuration is active.

The following command will show which configuration you are using:

```bash
gcloud config configurations list
```

### Create a regional IP address (and a DNS record)

The Kubernetes ingress used to access the OpenHexa notebooks component exposes an external IP. This IP might change 
when re-deploying or re-provisioning. In order to prevent it, create an address in GCP compute and get back its value:

```bash
gcloud compute addresses create <HEXA_NOTEBOOKS_ADDRESS_NAME> --region=europe-west1
gcloud compute addresses describe <HEXA_NOTEBOOKS_ADDRESS_NAME> --region=europe-west1
```

Then, you can create a DNS record that points to the ip address returned by the `describe` command above.

### Create a Cloud SQL instance, database and user

Unless you already have a ready-to-use Google Cloud SQL instance, you can create one using the following command:

```bash
gcloud sql instances create hexa-main \
 --database-version=POSTGRES_12 \
 --cpu=2 --memory=7680MiB --zone=europe-west1-b --root-password=asecurepassword
```

You will then need to create a database for the Notebooks component:

```bash
gcloud sql databases create hexa-notebooks --instance=hexa-main
```

You will need a user as well:

```bash
gcloud sql users create hexa-notebooks --instance=hexa-main --password=asecurepassword
```

🚨 The created user will have root access on your instance. You should make sure to adapt its permissions accordingly if
needed.

The last step is to get the connection string of your Cloud SQL instance. Launch the following command and write down
the value next to the `connectionName` key, you will need it later:

```bash
gcloud sql instances describe hexa-main
```

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