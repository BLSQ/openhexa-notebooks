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
  version           = "1.0.0"
  namespace         = data.kubernetes_namespace.notebooks.metadata[0].name
  dependency_update = true

  # Base value file
  values = [
    file("${path.module}/base_config.yaml"),
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
  set_sensitive { # TODO: use a secret and set PG env variables?
    name  = "hub.db.url"
    value = "postgresql://hexa-notebooks-${var.environment}@127.0.0.1:5432/hexa-notebooks-${var.environment}"
  }
  # see https://github.com/hashicorp/terraform-provider-helm/issues/628
  set {
    name  = "hub.extraFiles.jupyterhub_config.binaryData"
    value = base64encode(file("${path.module}/../../../jupyterhub/jupyterhub_config.py"))
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