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
# Cloud SQL instance
variable "gcp_sql_instance_name" {
  description = "The name of the GCP Cloud SQL instance"
  default     = "hexa-prime"
}
variable "gcp_sql_instance_tier" {
  description = "The tier to use for the Cloud SQL instance"
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
