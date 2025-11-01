# CI/CD con GitHub Actions

Este proyecto está configurado para desplegar automáticamente a Cloud Run cuando se hace push a `main`.

## 🔧 Configuración inicial requerida

### 1. Crear Service Account para GitHub Actions

```bash
# Crear service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account" \
  --project=spotgenai

# Dar permisos necesarios
gcloud projects add-iam-policy-binding spotgenai \
  --member="serviceAccount:github-actions-sa@spotgenai.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding spotgenai \
  --member="serviceAccount:github-actions-sa@spotgenai.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding spotgenai \
  --member="serviceAccount:github-actions-sa@spotgenai.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### 2. Configurar Workload Identity Federation

```bash
# Crear Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Actions Pool" \
  --project=spotgenai

# Crear Workload Identity Provider para GitHub
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'jordanScript'" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --project=spotgenai

# Permitir autenticación del repo específico
gcloud iam service-accounts add-iam-policy-binding github-actions-sa@spotgenai.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/350436320279/locations/global/workloadIdentityPools/github-pool/attribute.repository/jordanScript/agent-bff-service" \
  --project=spotgenai
```

### 3. Obtener valores para GitHub Secrets

```bash
# Obtener Workload Identity Provider
gcloud iam workload-identity-pools providers describe github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)" \
  --project=spotgenai
```

### 4. Configurar GitHub Secrets

Ve a tu repositorio en GitHub: **Settings > Secrets and variables > Actions**

Agrega estos secrets:

- `WIF_PROVIDER`: (El output del comando anterior, formato: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`)
- `WIF_SERVICE_ACCOUNT`: `github-actions-sa@spotgenai.iam.gserviceaccount.com`

## 🚀 Uso

Una vez configurado, el workflow se ejecutará automáticamente cuando:
- Hagas push a la rama `main`
- Ejecutes manualmente desde GitHub Actions tab

El workflow:
1. ✅ Construye la imagen Docker
2. ✅ La sube a Artifact Registry con tag del commit
3. ✅ Despliega a Cloud Run
4. ✅ Muestra la URL del servicio

## 📝 Variables de entorno

Puedes modificar estas variables en `.github/workflows/deploy.yml`:

- `PROJECT_ID`: ID del proyecto GCP
- `REGION`: Región de despliegue
- `SERVICE_NAME`: Nombre del servicio en Cloud Run
- `REPOSITORY`: Nombre del repositorio en Artifact Registry
