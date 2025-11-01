PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
REPO ?= agent-bff-cr
SERVICE ?= agent-bff-service
IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/$(SERVICE):latest

.PHONY: build submit tf-init tf-apply url

build:
	docker build -t $(IMAGE) .

submit:
	gcloud builds submit --config=cloudbuild.yaml --substitutions=_REGION=$(REGION),_REPO=$(REPO),_SERVICE=$(SERVICE)

tf-init:
	cd terraform && terraform init

tf-apply:
	cd terraform && terraform apply -auto-approve -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)" -var="service_name=$(SERVICE)" -var="container_image=$(IMAGE)"

url:
	gcloud run services describe $(SERVICE) --region=$(REGION) --format='value(status.url)'
