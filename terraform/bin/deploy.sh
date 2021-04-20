#!/bin/bash
output_file_path=$1
namespace=$2

# Export variables from output file
terraform output >> "$output_file_path"
if ( ! ( sed -i 's/ //g' "$output_file_path" && sed -i 's/"//g' "$output_file_path" ) ) 
then 
    echo "Sed Failure!"
    exit 1
fi
. $output_file_path

# Get the connection string of your Cloud SQL instance and add it into $output_file_path
gcloud sql instances describe $gcp_sql_database_name  >> test.yaml
ConnectionName=$(yq -r .connectionName test.yaml)
rm test.yaml
echo CLOUDSQL_CONNECTION_STRING=$ConnectionName >> "$output_file_path"


# Download a key file for the service account and keep it somewhere safe
mkdir -p ../gcp_keyfiles
gcloud iam service-accounts keys create ../gcp_keyfiles/hexa-cloud-sql-proxy.json \
  --iam-account=$gcp_service_account_email

# Make sure that the kubectl utility can access the newly created cluster
gcloud container clusters get-credentials $gcp_gke_cluster_name --region=$gcp_gke_cluster_zone
 
# Create a specific Kubernetes namespace
kubectl create namespace $namesapce

# Create a secret for the Cloud SQL proxy
kubectl create secret generic hexa-cloudsql-oauth-credentials -n $namespacee \
  --from-file=credentials.json=../gcp_keyfiles/hexa-cloud-sql-proxy.json

# Prepare the Helm values file
cp helm/sample_config.yaml helm/config.yaml
nano helm/config.yaml

# Transform output file to YAML
if ( ! ( sed -i 's/=/: /g' "$output_file_path" ) ) 
then 
    echo "Sed Failure!"
    exit 1
fi

# Update app file using Python

python update_app_file.py  \
  "$output_file_path" \
  "helm/config.yaml" \

# Deploy 
helm upgrade --cleanup-on-fail --install hexa-notebooks jupyterhub/jupyterhub \
  --namespace=$namespace \
  --version=0.11.1-n393.h2aa513d9 \
  --values=helm/config.yaml \
  --set-file=hub.extraFiles.jupyterhub_config.stringData=./jupyterhub/jupyterhub_config.py

kubectl rollout restart deployment/autohttps --namespace=$namespace        


