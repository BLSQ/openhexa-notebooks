
output "gcp_sql_database_name" {
  value = google_sql_database.hexa.name
}
output "gcp_sql_database_user" {
  value = google_sql_user.hexa.name
}
output "gcp_sql_database_password" {
  value = google_sql_user.hexa.password
}

output "gcp_gke_cluster_zone" {
  value = google_container_cluster.hexa.location
}
output "gcp_gke_cluster_name" {
  value = google_container_cluster.hexa.name
}
output "hexa_domain" {
  value = aws_route53_record.www.name
}
output "gcp_compute_address" {
  value = google_compute_address.hexa.address
}
output "gcp_service_account_email" {
  value = google_service_account.hexa.email
}
output "aws_route53_record_name" {
  value = aws_route53_record.www.name
}