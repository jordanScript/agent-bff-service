# Cloud Run (v2) service
resource "google_cloud_run_v2_service" "service" {
  provider            = google-beta
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = var.container_image

      env {
        name  = "SERVICE_NAME"
        value = var.service_name
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = "spotgenai"
      }

      env {
        name  = "VERTEX_LOCATION"
        value = "us-central1"
      }

      env {
        name  = "REASONING_ENGINE_ID"
        value = "5664318868441530368"
      }

      env {
        name  = "WHATSAPP_TOKEN"
        value = "EAAP3xrWu1p8BP2iLgTZBM1haUgx6W2yQsWSubZAU3pV4SjnKD59mz5k1BxaOhRCLXuLTqK6Nuzos5lZBuw5o5Sf8cURDeyUkVAWuZCZA1sDix9VIujfDbIMBqjZAo9pFMWS9FNxzX8y1GuaaMwEGdzKwZAyZCxHkZA8YstWaX0BApZACWZB4qZA3lQBpKomYZAesIkkO3UhM0hZAlVmhpHmxHdI67bZA4i1BeBhN5dQMuI8sV42n1ZBUf5Qi2EeZCKBAi3QZBQ2ldyFeTA15fZBrS5zNqnjJqGr"
      }

      env {
        name  = "WHATSAPP_PHONE_NUMBER_ID"
        value = "883518508167909"
      }

      env {
        name  = "WHATSAPP_VERIFY_TOKEN"
        value = "mi_token_secreto_12345"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      ports {
        container_port = 8080
      }
    }
  }

  # Ensure APIs enabled
  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.repo
  ]
}

# Allow unauthenticated invocation
resource "google_cloud_run_v2_service_iam_member" "unauth" {
  provider = google-beta
  name     = google_cloud_run_v2_service.service.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
