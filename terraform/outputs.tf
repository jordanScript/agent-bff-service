output "cloud_run_url" {
  description = "URL del servicio de Cloud Run"
  value       = google_cloud_run_v2_service.service.uri
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}
