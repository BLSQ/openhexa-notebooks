# Namespace
data "kubernetes_namespace" "notebooks" {
  metadata {
    name = "hexa-notebooks-${var.environment}"
  }
}

# Fetch networking resources
data "google_compute_address" "notebooks" {
  name = "hexa-notebooks-${var.environment}"
}

# Helm release
resource "helm_release" "notebooks" {
  chart             = "jupyterhub"
  repository        = "https://jupyterhub.github.io/helm-chart/"
  name              = "hexa-notebooks"
  version           = "1.1.1"  # should match the Docker image version we use for the hub as a basis
  namespace         = data.kubernetes_namespace.notebooks.metadata[0].name
  dependency_update = true

  values = [
    # Base value file
    file("${path.module}/base_config.yaml"),
    # The terraform helm provider cannot set int or float values, and that z2jh will not accept/convert
    # strings, so we need to use this workaround to set those values dynamically
    <<EOT
singleuser:
  cpu:
    guarantee: 0.05
    limit: ${var.user_cpu_limit}
  memory:
    guarantee: 64M
    limit: ${var.user_memory_limit}
EOT
  ]

  # Proxy
  set {
    name  = "proxy.https.hosts"
    value = "{${var.domain}}"
  }
  set {
    name  = "proxy.https.letsencrypt.contactEmail"
    value = var.certificate_contact_email
  }
  set {
    name  = "proxy.service.loadBalancerIP"
    value = data.google_compute_address.notebooks.address
  }

  # Hub
  set_sensitive {
    name  = "hub.db.url"
    value = "postgresql://hexa-notebooks-${var.environment}@127.0.0.1:5432/hexa-notebooks-${var.environment}"
  }
  set {
    name = "hub.image.name"
    value = var.hub_image_name
  }
  set {
    name = "hub.image.tag"
    value = var.hub_image_tag
  }

  # Single User
  set {
    name  = "singleuser.image.name"
    value = var.user_image_name
  }
  set {
    name  = "singleuser.image.tag"
    value = var.user_image_tag
  }
}
