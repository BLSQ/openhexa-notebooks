terraform {
  backend "s3" {
    encrypt = true
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.66.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.1.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "3.38.0"
    }
  }
}

# GCP
provider "google" {
  project = var.gcp_project_id
}
# Global IP address
resource "google_compute_address" "notebooks" {
  name   = var.gcp_address_name
  region = var.gcp_region
}


# If prevent_destroy is set to true, the deploy will fail 
# And the plan too when a resource which attribute (if changed) causes the resource to be destroyed and recreated.
# It is applied  for cluster, node pools, Database instances, Databases, Database users

# Cloud SQL
resource "google_sql_database_instance" "notebooks" {
  database_version = "POSTGRES_12"
  name             = var.gcp_sql_instance_name
  region           = var.gcp_region
  lifecycle {
    prevent_destroy = true
  }
  settings {
    tier              = var.gcp_sql_instance_tier
    availability_type = var.gcp_sql_instance_availability_type
    backup_configuration {
      enabled                        = var.gcp_sql_instance_backup_enabled
      point_in_time_recovery_enabled = var.gcp_sql_instance_point_in_time_recovery_enabled
    }
    ip_configuration {
      ipv4_enabled = true
      # TODO: find a safer way to access Cloud SQL instance
      authorized_networks {
        name  = "external-access"
        value = "0.0.0.0/0"
      }
    }
  }
}
resource "google_sql_database" "notebooks" {
  name     = var.gcp_sql_database_name
  instance = google_sql_database_instance.notebooks.name
  lifecycle {
    prevent_destroy = true
  }
}
resource "random_password" "notebooks_database" {
  length  = 20
  special = false
  lifecycle {
    ignore_changes = all
  }
}
resource "google_sql_user" "notebooks" {
  name     = var.gcp_sql_user_name
  instance = google_sql_database_instance.notebooks.name
  password = random_password.notebooks_database.result
  provisioner "local-exec" {
    command = <<EOT
      psql postgresql://${google_sql_user.notebooks.name}:${google_sql_user.notebooks.password}@${google_sql_database_instance.notebooks.public_ip_address}:5432/${google_sql_database.notebooks.name} <<EOT
      GRANT ALL PRIVILEGES ON DATABASE ${google_sql_database.notebooks.name} TO "${google_sql_user.notebooks.name}";
      GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${google_sql_user.notebooks.name}";
    EOT
  }
  lifecycle {
    prevent_destroy = true
  }
}
# IAM (Cloud SQL proxy)
resource "google_service_account" "notebooks_cloud_sql_proxy" {
  account_id   = var.gcp_iam_cloud_sql_proxy_service_account_id
  display_name = var.gcp_iam_cloud_sql_proxy_service_account_id
  project      = var.gcp_project_id
  description  = "Cloud SQL Proxy"
}
resource "google_service_account_key" "notebooks_cloud_sql_proxy" {
  service_account_id = google_service_account.notebooks_cloud_sql_proxy.name

  keepers = {
    # Keep the key alive as long as the service account ID stays the same
    service_account_id = google_service_account.notebooks_cloud_sql_proxy.account_id
  }
}
resource "google_project_iam_member" "notebooks_cloud_sql_proxy" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.notebooks_cloud_sql_proxy.email}"
}
# GKE cluster
# Please note that as we will share the cluster between the app and notebooks components, we need to declare
# all the node pools in the terraform config of both components - terraform cannot handle the node pools
# separately
resource "google_container_cluster" "cluster" {
  name                     = var.gcp_gke_cluster_name
  location                 = var.gcp_zone
  initial_node_count       = 1
  remove_default_node_pool = true
  lifecycle {
    ignore_changes  = [remove_default_node_pool]
    prevent_destroy = true
  }
}
resource "google_container_node_pool" "shared_pool" {
  cluster    = google_container_cluster.cluster.name
  name       = var.gcp_gke_shared_pool_name
  location   = var.gcp_zone
  node_count = 1
  autoscaling {
    min_node_count = 1
    max_node_count = var.gcp_gke_shared_pool_max_node_count
  }
  node_config {
    machine_type = var.gcp_gke_shared_pool_machine_type
    metadata = {
      disable-legacy-endpoints = true
    }
  }
  lifecycle {
    prevent_destroy = true
  }
}
resource "google_container_node_pool" "user_pool" {
  cluster    = google_container_cluster.cluster.name
  name       = var.gcp_gke_user_pool_name
  location   = var.gcp_zone
  node_count = 1
  autoscaling {
    min_node_count = 1
    max_node_count = var.gcp_gke_user_pool_max_node_count
  }
  node_config {
    machine_type = var.gcp_gke_user_pool_machine_type
    metadata = {
      disable-legacy-endpoints = true
    }
    taint {
      effect = "NO_SCHEDULE"
      key    = "hub.jupyter.org_dedicated"
      value  = "user"
    }
    labels = {
      "hub.jupyter.org/node-purpose" = "user"
    }
  }
  lifecycle {
    prevent_destroy = true
  }
}

# KUBERNETES
data "google_client_config" "terraform" {}
provider "kubernetes" {
  host  = "https://${google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.terraform.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.cluster.master_auth[0].cluster_ca_certificate,
  )
}
# Namespace
resource "kubernetes_namespace" "notebooks" {
  metadata {
    name = var.kubernetes_namespace
  }
}
# Secrets
resource "kubernetes_secret" "cloud_sql_proxy" {
  metadata {
    name      = "cloud-sql-proxy-secret"
    namespace = kubernetes_namespace.notebooks.metadata[0].name
  }
  # TODO: Use workload identity, see # https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
  data = {
    "credentials.json" = base64decode(google_service_account_key.notebooks_cloud_sql_proxy.private_key)
  }
}
# HELM
provider "helm" {
  kubernetes {
    host  = "https://${google_container_cluster.cluster.endpoint}"
    token = data.google_client_config.terraform.access_token
    cluster_ca_certificate = base64decode(
      google_container_cluster.cluster.master_auth[0].cluster_ca_certificate,
    )
  }
}
resource "random_id" "proxy_secret_token" {
  byte_length = 32
  lifecycle {
    ignore_changes = all
  }
}
resource "random_id" "hub_cookie_secret" {
  byte_length = 32
  lifecycle {
    ignore_changes = all
  }
}
resource "helm_release" "notebooks" {
  chart             = "jupyterhub"
  repository        = "https://jupyterhub.github.io/helm-chart/"
  name              = "hexa-notebooks"
  version           = "0.11.1-n438.h7e6a66e9"
  dependency_update = true
  namespace         = kubernetes_namespace.notebooks.metadata[0].name

  # Base value file
  values = [
    file("helm/base_config.yaml"),
    # set {} cannot handle numbers...
    <<EOF
singleuser:
  cpu:
    guarantee: ${var.helm_singleuser_cpu_guarantee}
    limit: ${var.helm_singleuser_cpu_limit}
  memory:
    guarantee: ${var.helm_singleuser_memory_guarantee}
    limit: ${var.helm_singleuser_memory_limit}
EOF
  ]

  # Proxy
  set {
    name  = "proxy.secretToken"
    value = random_id.proxy_secret_token.hex
  }
  set {
    name  = "proxy.https.hosts"
    value = "{${var.notebooks_domain}}"
  }
  set {
    name  = "proxy.https.letsencrypt.contactEmail"
    value = var.helm_proxy_https_letsencrypt_contact_email
  }
  set {
    name  = "proxy.service.loadBalancerIP"
    value = google_compute_address.notebooks.address
  }

  # Hub
  set {
    name  = "hub.cookieSecret"
    value = random_id.hub_cookie_secret.hex
  }
  set {
    name  = "hub.db.url"
    value = "postgresql://${google_sql_user.notebooks.name}:${google_sql_user.notebooks.password}@127.0.0.1:5432/${google_sql_database.notebooks.name}"
  }
  set {
    name  = "hub.extraContainers[0].command"
    value = "{/cloud_sql_proxy,--dir=/cloudsql,-instances=${google_sql_database_instance.notebooks.connection_name}=tcp:5432,-credential_file=/secrets/cloudsql/credentials.json}"
  }
  set {
    name  = "hub.extraVolumes[0].secret.secretName"
    value = kubernetes_secret.cloud_sql_proxy.metadata[0].name
  }
  set {
    name  = "hub.extraEnv.APP_URL"
    value = var.app_url
  }
  set {
    name  = "hub.extraEnv.APP_CREDENTIALS_URL"
    value = "${var.app_url}/notebooks/credentials/"
  }
  set {
    name  = "hub.extraEnv.CONTENT_SECURITY_POLICY"
    value = "frame-ancestors 'self' ${var.app_domain};"
  }
  # see https://github.com/hashicorp/terraform-provider-helm/issues/628
  set {
    name  = "hub.extraFiles.jupyterhub_config.binaryData"
    value = base64encode(file("../jupyterhub/jupyterhub_config.py"))
  }

  # Single User
  set {
    name  = "singleuser.image.name"
    value = var.notebooks_base_image_name
  }
  set {
    name  = "singleuser.image.tag"
    value = var.notebooks_base_image_tag
  }
  set {
    name  = "singleuser.extraEnv.CONTENT_SECURITY_POLICY"
    value = "frame-ancestors 'self' ${var.app_domain};"
  }
}

# AWS
provider "aws" {
  region = var.aws_region
}
# Route53 Record
data "aws_route53_zone" "zone" {
  name         = var.aws_route53_zone_name
  private_zone = false
}
resource "aws_route53_record" "notebooks" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = "${var.aws_route53_record_name}.${data.aws_route53_zone.zone.name}"
  type    = "A"
  ttl     = "300"
  records = [
    google_compute_address.notebooks.address
  ]
}
resource "aws_route53_record" "letsencrypt_caa" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = "${var.aws_route53_record_name}.${data.aws_route53_zone.zone.name}"
  type    = "CAA"
  ttl     = "300"
  records = [
    "0 issue \"letsencrypt.org\"",
  ]
}
