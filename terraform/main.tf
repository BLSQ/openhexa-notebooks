provider "google" {
  project = var.gcp_project_id
}

provider "aws" {
  region = "eu-central-1"
}

# Create a regional IP address (and a DNS record)
resource "google_compute_address" "hexa" {
  name   = var.gcp_global_address_name
  region = var.gcp_global_address_region
}

# Create a DNS record
data "aws_route53_zone" "blsq" {
  name         = "openhexa.org"
  private_zone = false
}
resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.blsq.zone_id
  name    = "${var.record_name}.test.${data.aws_route53_zone.blsq.name}"
  type    = "A"
  ttl     = "300"
  records = [
    google_compute_address.hexa.address
  ]
}

# Create a Cloud SQL instance, database and user
resource "google_sql_database_instance" "hexa" {
  name             = var.gcp_sql_instance_name
  database_version = "POSTGRES_12"
  region           = var.gcp_sql_instance_region
  root_password    = random_password.root_password.result
  settings {
    tier = var.gcp_sql_machine_type_tier
  }

}
resource "random_password" "root_password" {
  length  = 48
  special = false
}

resource "google_sql_database" "hexa" {
  name     = var.gcp_sql_database_name
  instance = google_sql_database_instance.hexa.name

}
resource "random_password" "user_password" {
  length  = 48
  special = false
}

resource "google_sql_user" "hexa" {
  name     = var.gcp_sql_user_name
  instance = google_sql_database_instance.hexa.name
  password = random_password.user_password.result
}

# Create a service account for the Cloud SQL proxy
resource "google_service_account" "hexa" {
  account_id   = var.account_id
  display_name = var.display_name
  project      = var.gcp_project_id
  description  = "Used to allow pods to access Cloud SQL"
}
resource "google_service_account_key" "hexa" {
  service_account_id = google_service_account.hexa.name
}
resource "google_project_iam_binding" "hexa" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  members = [
    "serviceAccount:${google_service_account.hexa.email}",
  ]
}

# Create a GKE cluster
resource "google_container_cluster" "hexa" {
  name     = var.gcp_gke_cluster_name
  location = var.gcp_gke_cluster_zone
  node_pool {
    name       = var.gcp_gke_default_pool_name
    node_count = 1
    autoscaling {
      max_node_count = 4
      min_node_count = 1
    }
    node_config {
      machine_type = var.gcp_gke_default_machine_type
      metadata = {
        disable-legacy-endpoints = true
      }
    }
  }
  lifecycle {
    ignore_changes = [ip_allocation_policy]
  }
}

resource "google_container_node_pool" "hexa" {
  name       = var.gcp_gke_user_node_pool_name
  location   = var.gcp_gke_user_node_pool_zone
  cluster    = google_container_cluster.hexa.name
  node_count = 1
  autoscaling {
    max_node_count = 4
    min_node_count = 1
  }

  node_config {
    machine_type = var.gcp_gke_user_machine_type
    taint {
      effect = var.gcp_gke_user_node_pool_taint_effect
      key    = var.gcp_gke_user_node_pool_taint_key
      value  = var.gcp_gke_user_node_pool_taint_value
    }
    labels = var.gcp_gke_user_node_pool_labels
  }
}