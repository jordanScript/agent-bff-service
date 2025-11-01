# FastAPI → Cloud Run (Terraform)

Proyecto mínimo para desplegar una API FastAPI en **Google Cloud Run** usando **Terraform** y **Artifact Registry**.

## Estructura
```
fastapi-cloudrun-terraform/
├── app/
│   └── main.py
├── Dockerfile
├── requirements.txt
├── cloudbuild.yaml
├── Makefile
└── terraform/
    ├── versions.tf
    ├── providers.tf
    ├── variables.tf
    ├── main.tf
    ├── artifact_registry.tf
    ├── service_account.tf
    ├── cloud_run.tf
    └── outputs.tf
```

## Prerrequisitos
- `gcloud` autenticado y con proyecto configurado (`gcloud config set project <PROJECT_ID>`)
- `terraform >= 1.5`
- Permisos de Owner/Editor o equivalentes en el proyecto.
- Habilitar facturación en el proyecto.

## Pasos de despliegue
1. **(Opcional) Ajusta variables** en `terraform/variables.tf` o usa `-var` con Terraform.
2. **Crea y sube la imagen** con Cloud Build (recom.):  
   ```bash
   make submit REGION=southamerica-west1 REPO=fastapi-cr SERVICE=fastapi-service
   ```
3. **Provisiona Cloud Run con Terraform**:
   ```bash
   make tf-init
   make tf-apply REGION=southamerica-west1 SERVICE=fastapi-service
   ```
4. **Obtén la URL**:
   ```bash
   make url REGION=southamerica-west1 SERVICE=fastapi-service
   ```

## Notas
- Terraform crea el repositorio de **Artifact Registry**, la **Service Account** de runtime, permisos, y el **servicio de Cloud Run**.
- La imagen que despliega Terraform viene de Artifact Registry: `${REGION}-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE:latest`.
- `cloudbuild.yaml` construye y empuja la imagen; también puedes usar `docker build` + `docker push` manualmente.
