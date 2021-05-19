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
  }
}
provider "google" {
  project = var.gcp_project_id
}
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
resource "google_container_cluster" "cluster" {
  name                     = var.gcp_gke_cluster_name
  location                 = var.gcp_zone
  initial_node_count       = 1
  remove_default_node_pool = true
  lifecycle {
    ignore_changes = [remove_default_node_pool]
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
