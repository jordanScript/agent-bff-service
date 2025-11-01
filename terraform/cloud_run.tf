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
