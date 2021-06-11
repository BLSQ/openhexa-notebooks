terraform {
  backend "gcs" {
    prefix = "releases/demo/notebooks"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.71.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.3.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.1.2"
    }
  }
}

# Providers configuration
provider "google" {}
data "google_client_config" "config" {}
data "google_container_cluster" "aldebaran" {
  name = "hexa-aldebaran"
}
data "google_sql_database_instance" "sirius" {
  name = "hexa-sirius"
}
provider "kubernetes" {
  host  = "https://${data.google_container_cluster.aldebaran.endpoint}"
  token = data.google_client_config.config.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.aldebaran.master_auth[0].cluster_ca_certificate,
  )
}
provider "helm" {
  kubernetes {
    host  = "https://${data.google_container_cluster.aldebaran.endpoint}"
    token = data.google_client_config.config.access_token
    cluster_ca_certificate = base64decode(
      data.google_container_cluster.aldebaran.master_auth[0].cluster_ca_certificate,
    )
  }
}

# Release
module "release" {
  source            = "../modules/release"
  environment       = "demo"
  domain            = "notebooks.demo.openhexa.org"
  user_image_tag    = "0.3.2"
  user_cpu_limit    = 2
  user_memory_limit = "4G"
}
