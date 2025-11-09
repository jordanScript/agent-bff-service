#!/bin/bash

# Script to configure GitHub secrets and variables for CI/CD
# This script should be run after applying Terraform

set -e

echo "🔍 Getting Terraform outputs..."
cd terraform

# Get values from Terraform
PROJECT_NUMBER=$(gcloud projects describe spotgenai --format="value(projectNumber)")
WIF_PROVIDER=$(terraform output -raw wif_provider_name)
SA_EMAIL=$(terraform output -raw github_actions_sa_email)
REGION=$(terraform output -raw region)

cd ..

echo "📝 Setting GitHub secrets..."
gh secret set WIF_PROVIDER --body "${WIF_PROVIDER}"
gh secret set SERVICE_ACCOUNT_EMAIL --body "${SA_EMAIL}"

echo "📝 Setting GitHub variables..."
gh variable set PROJECT_ID --body "spotgenai"
gh variable set PROJECT_NUMBER --body "${PROJECT_NUMBER}"
gh variable set REGION --body "${REGION}"
gh variable set SERVICE_NAME --body "agent-bff-service"
gh variable set ARTIFACT_REGISTRY --body "${REGION}-docker.pkg.dev/spotgenai/agent-bff-cr"

echo ""
echo "✅ GitHub secrets and variables configured!"
echo ""
echo "Configured secrets:"
echo "  - WIF_PROVIDER"
echo "  - SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Configured variables:"
echo "  - PROJECT_ID: spotgenai"
echo "  - PROJECT_NUMBER: ${PROJECT_NUMBER}"
echo "  - REGION: ${REGION}"
echo "  - SERVICE_NAME: agent-bff-service"
echo "  - ARTIFACT_REGISTRY: ${REGION}-docker.pkg.dev/spotgenai/agent-bff-cr"
