variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "region" {
  description = "Región para Cloud Run/Artifact Registry (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Nombre del servicio de Cloud Run"
  type        = string
  default     = "agent-bff-service"
}

variable "repository_id" {
  description = "ID del repositorio en Artifact Registry"
  type        = string
  default     = "agent-bff-cr"
}

variable "container_image" {
  description = "Ruta completa de la imagen a desplegar (e.g., us-central1-docker.pkg.dev/PROJECT/REPO/SERVICE:latest)"
  type        = string
}
