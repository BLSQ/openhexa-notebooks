variable "notebooks_domain" {
  description = "The fully-qualified domain name of the notebooks component"
}
variable "app_domain" {
  description = "The fully-qualified domain name of the app component"
}
variable "app_url" {
  description = "The full URL of the app component"
}
variable "notebooks_base_image_name" {
  description = "The base Docker image to use for the notebooks component"
  default     = "blsq/openhexa-base-notebook"
}
variable "notebooks_base_image_tag" {
  description = "The tag of the Docker image for the notebooks component"
  default     = "latest"
}

# GCP
variable "gcp_project_id" {
  description = "The ID of your Google Cloud Platform project"
}
variable "gcp_region" {
  description = "The name of the region to use for GCP resources"
}
variable "gcp_zone" {
  description = "The name of the zone to use for GCP resources"
}

# Global IP address
variable "gcp_address_name" {
  description = "The name of the GCP global address to use for the notebooks component"
}

# Cloud SQL instance
variable "gcp_sql_instance_name" {
  description = "The name of the GCP Cloud SQL instance"
  default     = "hexa-prime"
}
variable "gcp_sql_instance_tier" {
  description = "The tier to use for the Cloud SQL instance"
  default     = "db-custom-1-3840"
}
variable "gcp_sql_instance_availability_type" {
  description = "The availability type for the master instance.This is only used to set up high availability for the PostgreSQL instance. Can be either `ZONAL` or `REGIONAL`."
  type        = string
  default     = "ZONAL"
}
variable "gcp_sql_database_name" {
  description = "The name of the notebooks component database"
  default     = "hexa-notebooks"
}
variable "gcp_sql_user_name" {
  description = "The username for the notebooks component database"
  default     = "hexa-notebooks"
}

# Service account for the Cloud SQL proxy
variable "gcp_iam_cloud_sql_proxy_service_account_id" {
  description = "The ID of the service account used for the Cloud SQL proxy"
  default     = "hexa-notebooks-csp"
}

# GKE cluster
variable "gcp_gke_cluster_name" {
  description = "The name of the Kubernetes cluster in GKE"
  default     = "hexa-prime"
}
variable "gcp_gke_shared_pool_name" {
  description = "The name of the shared node pool (app & notebooks)"
  default     = "shared-pool"
}
variable "gcp_gke_shared_pool_max_node_count" {
  description = "The max number of nodes in the shared pool"
  default     = 3
}
variable "gcp_gke_shared_pool_machine_type" {
  description = "The machine type to use for nodes in the shared pool"
  default     = "e2-standard-2"
}
variable "gcp_gke_user_pool_name" {
  description = "The name of the user node pool"
  default     = "user-pool"
}
variable "gcp_gke_user_pool_max_node_count" {
  description = "The max number of nodes in the user pool"
  default     = 3
}
variable "gcp_gke_user_pool_machine_type" {
  description = "The machine type to use for nodes in the user pool"
  default     = "e2-highmem-2"
}

# KUBERNETES
variable "kubernetes_namespace" {
  description = "The namespace in which to deploy the resources of the notebooks component"
  default     = "hexa-notebooks"
}
variable "helm_proxy_https_letsencrypt_contact_email" {
  description = "The contact email address for the letsencrypt certificate"
}
variable "helm_singleuser_cpu_guarantee" {
  description = "The minimum fraction of CPU guaranteed for notebook servers"
  default     = 0.05
}
variable "helm_singleuser_cpu_limit" {
  description = "The max fraction of CPU available for notebook servers"
  default     = 1
}
variable "helm_singleuser_memory_guarantee" {
  description = "The minimum amount of memory guaranteed for notebook servers"
  default     = "64M"
}
variable "helm_singleuser_memory_limit" {
  description = "The max amount of memory available for notebook servers"
  default     = "512M"
}

# AWS
variable "aws_region" {
  description = "The name of the region to use for AWS resources"
}
# Route53
variable "aws_route53_zone_name" {
  description = "The name of the Route53 hosted zone"
}
variable "aws_route53_record_name" {
  description = "The record to add in the hosted zone"
}
