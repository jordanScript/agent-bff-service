output "cloud_run_url" {
  description = "URL del servicio de Cloud Run"
  value       = google_cloud_run_v2_service.service.uri
}
