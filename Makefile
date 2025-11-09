PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
REPO ?= agent-bff-cr
SERVICE ?= agent-bff-service
IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/$(SERVICE):latest

.PHONY: help build submit tf-init tf-apply tf-plan setup-cicd url test-local clean

help:
	@echo "Available commands:"
	@echo "  make build        - Build Docker image locally"
	@echo "  make test-local   - Run service locally with Docker"
	@echo "  make tf-init      - Initialize Terraform"
	@echo "  make tf-plan      - Preview Terraform changes"
	@echo "  make tf-apply     - Apply Terraform changes"
	@echo "  make setup-cicd   - Setup CI/CD with GitHub Actions (WIF)"
	@echo "  make url          - Get Cloud Run service URL"
	@echo "  make submit       - Submit build to Cloud Build (legacy)"
	@echo "  make clean        - Clean local Docker images"

build:
	docker build -t $(IMAGE) .

test-local:
	@echo "🚀 Running service locally on port 8080..."
	docker build -t $(SERVICE):local .
	docker run -p 8080:8080 --env-file .env $(SERVICE):local

submit:
	@echo "⚠️  Warning: This uses Cloud Build. Consider using GitHub Actions instead."
	gcloud builds submit --config=cloudbuild.yaml --substitutions=_REGION=$(REGION),_REPO=$(REPO),_SERVICE=$(SERVICE)

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)" -var="service_name=$(SERVICE)" -var="container_image=$(IMAGE)"

tf-apply:
	cd terraform && terraform apply -auto-approve -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)" -var="service_name=$(SERVICE)" -var="container_image=$(IMAGE)"

setup-cicd:
	@echo "🔧 Setting up CI/CD with GitHub Actions..."
	@echo ""
	@echo "Step 1: Applying Terraform (WIF, Service Accounts, etc.)..."
	@$(MAKE) tf-apply
	@echo ""
	@echo "Step 2: Configuring GitHub secrets and variables..."
	@./scripts/setup-github-secrets.sh
	@echo ""
	@echo "✅ CI/CD setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. git add ."
	@echo "  2. git commit -m 'feat: configure CI/CD with Workload Identity Federation'"
	@echo "  3. git push origin main"
	@echo ""
	@echo "The first push will trigger automatic deployment to Cloud Run! 🚀"

url:
	@gcloud run services describe $(SERVICE) --region=$(REGION) --format='value(status.url)'

clean:
	docker rmi $(IMAGE) $(SERVICE):local || true
