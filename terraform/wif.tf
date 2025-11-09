# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ==============================================================================
# Workload Identity Federation for GitHub Actions
# ==============================================================================

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-wif-pool-bff"
  display_name              = "GitHub Actions Pool for BFF"
  description               = "Workload Identity Pool for GitHub Actions authentication"
  project                   = var.project_id
}

# Workload Identity Provider (OIDC for GitHub Actions)
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider-bff"
  display_name                       = "GitHub Provider for BFF"
  description                        = "OIDC provider for GitHub Actions"
  project                            = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Restrict to specific repository
  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions_sa" {
  account_id   = "github-actions-bff"
  display_name = "GitHub Actions Service Account for BFF"
  description  = "Service account used by GitHub Actions to deploy BFF service"
  project      = var.project_id
}

# IAM Permissions for GitHub Actions Service Account
resource "google_project_iam_member" "github_actions_permissions" {
  for_each = toset([
    "roles/run.admin",                    # Manage Cloud Run services
    "roles/iam.serviceAccountUser",       # Act as service account
    "roles/artifactregistry.writer",      # Push images to Artifact Registry
    "roles/storage.objectViewer",         # Read from GCS if needed
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Allow GitHub Actions to impersonate the service account via WIF
resource "google_service_account_iam_member" "wif_sa_binding" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"
}

# ==============================================================================
# Outputs for GitHub Actions Configuration
# ==============================================================================

output "wif_provider_name" {
  description = "Full resource name of the Workload Identity Provider"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "github_actions_sa_email" {
  description = "Email of the GitHub Actions service account"
  value       = google_service_account.github_actions_sa.email
}

output "workload_identity_pool_id" {
  description = "ID of the Workload Identity Pool"
  value       = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
}

output "workload_identity_provider_id" {
  description = "ID of the Workload Identity Provider"
  value       = google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id
}
