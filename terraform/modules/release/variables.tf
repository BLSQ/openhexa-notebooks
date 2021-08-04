variable "environment" {
  description = "The OpenHexa environment identifier"
  type        = string
}
variable "domain" {
  description = "The domain through with the app component will be accessed"
  type        = string
}
variable "hub_image_name" {
  description = "The name of the hub image to use"
  type        = string
  default     = "blsq/openhexa-jupyterhub"
}
variable "hub_image_tag" {
  description = "The tag of the hub image to use"
  type        = string
}
variable "user_image_name" {
  description = "The name of the single-user server image to use"
  type        = string
  default     = "blsq/openhexa-base-notebook"
}
variable "user_image_tag" {
  description = "The tag of the single-user server image to use"
  type        = string
}
variable "user_cpu_limit" {
  description = "The max number of vCPU the user can use"
  type        = number
  default     = 1
}
variable "user_memory_limit" {
  description = "The max amount of memory the user can use"
  type        = string
  default     = "512M"
}
variable "certificate_contact_email" {
  description = "The contact email for the letsencrypt certificate"
  default     = "tech@bluesquarehub.com"
}
