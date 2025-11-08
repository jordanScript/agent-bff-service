# 🤖 Agent BFF Service

Backend for Frontend (BFF) para comunicación con Vertex AI Agent Engine y WhatsApp Business API.

## 🎯 Características

- ✅ Integración con Vertex AI Agent Engine (Reasoning Engine)
- ✅ WhatsApp Business API webhook
- ✅ **🎤 Transcripción de audio a texto con Google Cloud Speech-to-Text**
- ✅ Gestión de sesiones por usuario
- ✅ Despliegue en Cloud Run con Terraform
- ✅ CI/CD con GitHub Actions

## 📁 Estructura

```
agent-bff-service/
├── app/
│   ├── main.py                    # API principal con FastAPI
│   └── services/
│       ├── __init__.py
│       └── speech_service.py      # Servicio de Speech-to-Text
├── terraform/                      # Infraestructura como código
│   ├── main.tf                    # APIs habilitadas
│   ├── cloud_run.tf               # Configuración Cloud Run
│   ├── service_account.tf         # Service Account con permisos
│   └── ...
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD pipeline
├── Dockerfile
├── requirements.txt
├── .env                           # Variables de entorno
├── test_speech.sh                 # Script de prueba
└── README.md
```

## 🎤 Procesamiento de Audio

El servicio ahora puede **transcribir mensajes de voz de WhatsApp** usando Google Cloud Speech-to-Text:

### Flujo de Audio

1. **Usuario envía audio** por WhatsApp
2. **BFF descarga el audio** desde WhatsApp API
3. **Speech-to-Text transcribe** el audio a texto
4. **Texto se envía al agente** como mensaje normal
5. **Respuesta del agente** se envía por WhatsApp

### Características de la Transcripción

- 🌍 **Idioma**: Español (es-US) por defecto, configurable
- 📝 **Puntuación automática**: Agrega puntos y comas
- 🎯 **Confianza**: Mide precisión de la transcripción (0-100%)
- ⚠️ **Notificación**: Informa al usuario cuando confianza es baja (<70%)
- 🔊 **Formato**: Soporta OGG Opus (formato nativo de WhatsApp)

## 🚀 Configuración Inicial

### 1. Prerrequisitos

```bash
# Verificar instalaciones
python --version          # Python 3.11+
gcloud --version         # Google Cloud SDK
terraform --version      # Terraform 1.5+
```

### 2. Configurar Proyecto GCP

```bash
# Establecer proyecto
gcloud config set project spotgenai

# Habilitar APIs necesarias
gcloud services enable speech.googleapis.com --project=spotgenai
gcloud services enable run.googleapis.com --project=spotgenai
gcloud services enable cloudbuild.googleapis.com --project=spotgenai
```

### 3. Configurar Permisos IAM

```bash
# Obtener cuenta activa
USER_EMAIL=$(gcloud config get-value account)

# Asignar permisos de Speech-to-Text
gcloud projects add-iam-policy-binding spotgenai \
  --member="user:$USER_EMAIL" \
  --role="roles/speech.client"

# Asignar permisos de Vertex AI
gcloud projects add-iam-policy-binding spotgenai \
  --member="user:$USER_EMAIL" \
  --role="roles/aiplatform.user"
```

### 4. Configurar Autenticación Local

```bash
# Configurar Application Default Credentials
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --project=spotgenai

# Configurar quota project
gcloud auth application-default set-quota-project spotgenai
```

### 5. Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 6. Configurar Variables de Entorno

Crear archivo `.env` con:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=spotgenai
VERTEX_LOCATION=us-central1
REASONING_ENGINE_ID=tu_reasoning_engine_id

# WhatsApp
WHATSAPP_TOKEN=tu_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_VERIFY_TOKEN=tu_verify_token

# Speech-to-Text
SPEECH_LANGUAGE_CODE=es-US
SPEECH_CONFIDENCE_THRESHOLD=0.7
```

## 🧪 Pruebas

### Verificar Configuración

```bash
# Ejecutar script de verificación
./test_speech.sh
```

### Ejecutar Localmente

```bash
# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --port 8080

# En otra terminal, probar el endpoint
curl http://localhost:8080/
curl http://localhost:8080/healthz
```

### Probar con WhatsApp

1. Configura el webhook de WhatsApp apuntando a tu URL
2. Envía un **mensaje de texto** → Respuesta normal
3. Envía un **mensaje de voz** → Se transcribe y responde

## 🏗️ Despliegue

### Opción 1: Deploy con Terraform

```bash
cd terraform

# Inicializar Terraform
terraform init

# Ver cambios
terraform plan

# Aplicar cambios
terraform apply
```

### Opción 2: Deploy Manual con gcloud

```bash
# Build y deploy directo
gcloud run deploy agent-bff-service \
  --source . \
  --region us-central1 \
  --project spotgenai \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=spotgenai,VERTEX_LOCATION=us-central1
```

### Opción 3: CI/CD con GitHub Actions

El pipeline se ejecuta automáticamente al hacer push a `main`:

1. Build de la imagen Docker
2. Push a Artifact Registry
3. Deploy a Cloud Run

## 📊 Endpoints

### API Principal

- `GET /` - Info del servicio
- `GET /healthz` - Health check
- `POST /chat` - Chat con el agente
- `GET /agent/info` - Info del agente configurado

### WhatsApp Integration

- `GET /webhook` - Verificación de webhook (Meta)
- `POST /webhook` - Recibir mensajes de WhatsApp
  - ✅ Texto
  - ✅ **Audio (voz)** → Transcripción automática
- `GET /whatsapp/sessions` - Listar sesiones activas
- `DELETE /whatsapp/sessions/{phone}` - Eliminar sesión

## 🔍 Logs y Monitoreo

### Ver Logs Locales

```bash
# Los logs se muestran en la consola con emojis:
# 📩 Webhook recibido
# 🎤 Procesando audio
# ✅ Transcripción exitosa
# ❌ Error
```

### Ver Logs en Cloud Run

```bash
# Logs del servicio
gcloud run services logs read agent-bff-service \
  --region=us-central1 \
  --project=spotgenai
```

## 💰 Costos

### Speech-to-Text

- **Gratis**: Primeros 60 minutos/mes
- **Audio corto** (<60 seg): $0.006 por 15 segundos
- **Audio largo** (>60 seg): $0.009 por 15 segundos

Ejemplo: 1000 mensajes de voz de 30 seg = ~$12/mes (después de gratis)

### Cloud Run

- **Gratis**: 2M requests/mes, 360K GB-segundos/mes
- **Facturación**: Solo por uso real

## 🛠️ Troubleshooting

### Error: "Speech API not enabled"

```bash
gcloud services enable speech.googleapis.com --project=spotgenai
```

### Error: "Permission denied"

```bash
# Verificar permisos
gcloud projects get-iam-policy spotgenai \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"

# Agregar permisos necesarios
gcloud projects add-iam-policy-binding spotgenai \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/speech.client"
```

### Error: "Could not download audio"

- Verifica que el `WHATSAPP_TOKEN` sea válido
- Verifica que el audio_id existe
- Revisa los logs para más detalles

### Transcripción con baja confianza

- Pide al usuario que hable más claro
- Verifica el idioma configurado (`SPEECH_LANGUAGE_CODE`)
- Revisa que el audio tenga buena calidad

## 📚 Documentación Adicional

- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/docs)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/agents)
- [FastAPI](https://fastapi.tiangolo.com/)

## 🤝 Soporte

Para problemas o preguntas:
1. Revisa los logs: `./test_speech.sh`
2. Verifica la configuración de `.env`
3. Consulta la documentación oficial de GCP
