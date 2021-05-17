terraform {
  backend "s3" {
    bucket  = "terraform-openhexa-notebooks-state"
    key     = "openhexa-notebooks-test/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true
  }
}

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
  settings {
    tier                           = var.gcp_sql_machine_type_tier
    enabled                        = true
    point_in_time_recovery_enabled = true
    ip_configuration {
      ipv4_enabled = true

    }
  }
}
resource "google_sql_database" "hexa" {
  name     = var.gcp_sql_database_name
  instance = google_sql_database_instance.hexa.name

}
resource "random_password" "user_password" {
  length  = 20
  special = false
  lifecycle {
    ignore_changes = all
  }
}

resource "google_sql_user" "hexa" {
  name     = var.gcp_sql_user_name
  instance = google_sql_database_instance.hexa.name
  password = random_password.user_password.result
  provisioner "local-exec" {
    command = <<EOT
      psql postgresql://${google_sql_user.hexa.name}:${google_sql_user.hexa.password}@${google_sql_database_instance.hexa.public_ip_address}:5432/${google_sql_database.hexa.name} <<EOT
      GRANT ALL PRIVILEGES ON DATABASE ${google_sql_database.hexa.name} TO "${google_sql_user.hexa.name}";
      GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${google_sql_user.hexa.name}";
    EOT
  }
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
  # Default Node Pool
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
  # User Node Pool
  node_pool {
    name       = var.gcp_gke_user_node_pool_name
    node_count = 1
    autoscaling {
      max_node_count = 4
      min_node_count = 1
    }
    node_config {
      machine_type = var.gcp_gke_user_machine_type
      metadata = {
        disable-legacy-endpoints = true
      }
      taint {
        effect = var.gcp_gke_user_node_pool_taint_effect
        key    = var.gcp_gke_user_node_pool_taint_key
        value  = var.gcp_gke_user_node_pool_taint_value
      }
      labels = var.gcp_gke_user_node_pool_labels
    }
  }

}
provider "kubernetes" {
  load_config_file = true
}
# Create namespace
resource "kubernetes_namespace" "hexa" {
  metadata {
    name = var.kubernetes_namespace_name
  }
}
resource "null_resource" "hexa" {
  provisioner "local-exec" {
    command = <<EOT
      mkdir -p ../gcp_keyfiles 
      gcloud iam service-accounts keys create ../gcp_keyfiles/hexa-cloud-sql-proxy.json --iam-account=hexa-cloud-sql-proxy@blsq-dip-test.iam.gserviceaccount.com    
      EOT
  }
}
# Create a secret for the Cloud SQL proxy
resource "kubernetes_secret" "sql_proxy" {
  metadata {
    name      = var.kubernetes_secret_sql_proxy_name
    namespace = var.kubernetes_namespace_name
  }
  data = {
    "credentials.json" = file("../gcp_keyfiles/hexa-cloud-sql-proxy.json")
  }
}
