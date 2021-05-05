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
# Cloud SQL
resource "google_sql_database_instance" "notebooks" {
  database_version = "POSTGRES_12"
  name             = var.gcp_sql_instance_name
  region           = var.gcp_region
  settings {
    tier = var.gcp_sql_instance_tier
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
# GKE cluster
resource "google_container_cluster" "cluster" {
  name     = var.gcp_gke_cluster_name
  location = var.gcp_zone
  # Default node pool
  node_pool {
    name       = var.gcp_gke_default_pool_name
    node_count = 1
    autoscaling {
      min_node_count = 1
      max_node_count = var.gcp_gke_default_pool_max_node_count
    }
    node_config {
      machine_type = var.gcp_gke_default_pool_machine_type
      metadata = {
        disable-legacy-endpoints = true
      }
    }
  }
  # User node pool
  node_pool {
    name       = var.gcp_gke_user_pool_name
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
  }
}
