<div align="center">
   <img alt="OpenHexa Logo" src="https://openhexa.bluesquare.org/static/img/logo/logo_with_text_black.svg" height="80">
</div>

OpenHexa Notebooks Component
============================

OpenHexa is an **open-source data integration platform** that allows users to:

- Explore data coming from a variety of sources in a **data catalog**
- Schedule **data pipelines** for extraction & transformation operations
- Perform data analysis in **notebooks**
- Create rich data **visualizations**

<div align="center">
   <img alt="OpenHexa Screenshot" src="https://openhexa.bluesquare.org/static/img/screenshots/datasource_detail.png" hspace="10" height="150">
   <img alt="OpenHexa Screenshot" src="https://openhexa.bluesquare.org/static/img/screenshots/notebooks.png" hspace="10" height="150">
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

### Create a service account for the Cloud SQL proxy

The OpenHexa app component will connect to the Cloud SQL instance using a
[Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy). The proxy requires a GCP service account. If 
you have not created such a service account yet, create one:

```bash
gcloud iam service-accounts create hexa-cloud-sql-proxy \
  --display-name=hexa-cloud-sql-proxy \
  --description='Used to allow pods to access Cloud SQL'
```

Give it the `roles/cloudsql.client` role:

```bash
gcloud projects add-iam-policy-binding blsq-dip-test \
    --member=serviceAccount:hexa-cloud-sql-proxy@blsq-dip-test.iam.gserviceaccount.com \
    --role=roles/cloudsql.client
```

Finally, download a key file for the service account and keep it somewhere safe, we will need it later:

```bash
mkdir -p ../gcp_keyfiles
gcloud iam service-accounts keys create ../gcp_keyfiles/hexa-cloud-sql-proxy.json \
  --iam-account=hexa-cloud-sql-proxy@blsq-dip-test.iam.gserviceaccount.com
```

Note that we deliberately download the key file outside the current repository to avoid it being included 
in Git or in the Docker image.

### Create a GKE cluster:

Unless you already have a running Kubernetes cluster, you need to create one. The following command 
will create a new cluster in Google Kubernetes Engine, along with a default node pool:

```bash
gcloud container clusters create hexa-main \
  --machine-type=n2-standard-2 \
  --zone=europe-west1-b \
  --enable-autoscaling \
  --num-nodes=1 \
  --min-nodes=1 \
  --max-nodes=4 \
  --cluster-version=latest
```

The default node pool will be used by JupyterHub. The single-user Jupyter server pods can run in the default pool, but 
for performance considerations, we recommend creating a dedicated pool for them, with a more performant machine type:

```bash
gcloud container node-pools create user-pool-n2h2 \
  --cluster hexa-main \
  --machine-type=n2-highmem-2 \
  --zone=europe-west1-b \
  --enable-autoscaling \
  --num-nodes=1 \
  --min-nodes=1 \
  --max-nodes=4 \
  --node-labels=hub.jupyter.org/node-purpose=user \
  --node-taints=hub.jupyter.org_dedicated=user:NoSchedule
```

The `node-labels` and `node-taints` options will allow JupyterHub to spawn the single-user Jupyter server pods in the 
user node pool.

To make sure that the `kubectl` utility can access the newly created cluster, you need to launch another command:

```bash
gcloud container clusters get-credentials hexa-main --region=europe-west1-b
```

Deploying
---------

### Prepare the cluster

Before going further, check that `kubectl` is configured to use the proper cluster:

```bash
kubectl config current-context
```

Create a new namespace for the Notebooks component:

```bash
kubectl create namespace hexa-notebooks
```

Before we can deploy the Notebooks component, we need to create a secret for the Cloud SQL proxy:

```bash
kubectl create secret generic hexa-cloudsql-oauth-credentials -n hexa-notebooks \
  --from-file=credentials.json=../gcp_keyfiles/hexa-cloud-sql-proxy.json
```

### Prepare the Helm values file

We will deploy the Notebooks component with the `helm` utility. The Helm chart is deployed using a Helm values file 
that provide the necessary customizations. We provide a sample `helm/sample_config.yaml` file to serve as a basis.

Copy the sample value files and adapt it to your needs:

```bash
cp helm/sample_config.yaml helm/config.yaml
nano helm/config.yaml
```

Most of the placeholders in the sample file are self-explanatory. A few notes about some of them:

1. `HEXA_NOTEBOOKS_PROXY_SECRET_TOKEN` and `HEXA_NOTEBOOKS_HUB_COOKIE_SECRET` can be generated 
   using the `openssl rand -hex 32` command
1. For `HEXA_NOTEBOOKS_PROXY_SERVICE_LOAD_BALANCER_IP`, use the value of the static IP address created earlier
1. `HEXA_NOTEBOOKS_DOMAIN` is the qualified domain name for the **Notebooks component** itself, without `https://`
1. `CLOUDSQL_CONNECTION_STRING` can be obtained using the `gcloud sql instances describe hexa-main` command mentioned
   earlier
1. `HEXA_APP_DOMAIN` is the qualified domain name for the **App component** 
   (see [https://github.com/blsq/openhexa-app](https://github.com/blsq/openhexa-app)) 
1. You can use `HEXA_NOTEBOOKS_IMAGE_NAME` to specify which image to use for single-user Jupyter server
   ([blsq/openhexa-base-notebook](https://hub.docker.com/r/blsq/openhexa-base-notebook) is a sensible default)

### Deploy

You can them deploy the Helm chart in your cluster:

```bash
helm upgrade --cleanup-on-fail --install hexa-notebooks jupyterhub/jupyterhub \
  --namespace=hexa-notebooks \
  --version=0.11.1-n393.h2aa513d9 \
  --values=helm/config.yaml \
  --set-file=hub.extraFiles.jupyterhub_config.stringData=./jupyterhub/jupyterhub_config.py
```

There is currently an issue with the `autohttps` pod, which seems to start too early (before the successful deployment 
of the load balancer), resulting in the inability to provision the certificate. After a first deployment, you will 
have to restart it: 

```bash
kubectl rollout restart deployment/autohttps --namespace=hexa-notebooks        
```

Authentication
--------------

The **Notebooks component** uses a custom authenticator that will connect to the 
(**App component**)[https://github.com/blsq/openhexa-app] to authenticate users. You will need to have the App 
component up-and-running to be able to authenticate users.

Data stores
-----------

When the **Notebooks component** authenticates a user through the **App component**, it will also receive a set of 
environment variables that can be used to connect to external data stores:

- AWS S3 Bucket names and associated credentials (mounted on notebook servers using 
  [s3contents](https://github.com/danielfrg/s3contents))
- PostgreSQL database connection strings (users will have to use [SQLAlchemy](https://github.com/sqlalchemy) to connect 
  to those)

Building the Docker image
-------------------------

The OpenHexa Notebooks base Docker image is publicly available on Docker Hub
([blsq/openhexa-base-notebook](https://hub.docker.com/r/blsq/openhexa-base-notebook)).

This repository also provides a Github workflow to build the Docker image in the `.github/workflows` directory.

Uninstalling
------------

You can uninstall the Helm release and delete the Kubernetes namespace using the following commands:

```bash
helm uninstall hexa-notebooks --namespace=hexa-notebooks
kubectl delete namespace hexa-notebooks
```

Please note that this will only delete the deployment and the namespace, not resources provisioned for the project.

Local development
-----------------

This repository provides a ready-to-use `docker-compose.yaml` file for local development. It assumes that the 
[App component](https://github.com/blsq/openhexa-app) is running on [http://localhost:8000](http://localhost:8000).

Build the images, and you are ready to go:

```bash
docker-compose build
docker-compose up
```