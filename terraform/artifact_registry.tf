# Artifact Registry repository for container images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Repository for Cloud Run FastAPI images"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# Grant Cloud Build SA permission to push to Artifact Registry
data "google_project" "project" {}

resource "google_artifact_registry_repository_iam_member" "cb_writer" {
  location   = google_artifact_registry_repository.repo.location
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}
