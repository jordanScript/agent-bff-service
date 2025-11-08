# 📱 WhatsApp Integration Setup

## Overview

Este servicio integra WhatsApp Business API con el agente de Vertex AI, permitiendo que los usuarios conversen con el agente directamente desde WhatsApp.

## Arquitectura

```
Usuario WhatsApp → WhatsApp Business API → Webhook (BFF) → Vertex AI Agent → Respuesta
```

## Credenciales

- **Token de acceso**: `EAAP3xrWu1p8...` (configurado en variables de entorno)
- **Phone Number ID**: `883518508167909`
- **Business Account ID**: `1137412681919225`
- **Verify Token**: `mi_token_secreto_12345` (para verificación del webhook)

## Endpoints

### 1. Verificación del Webhook (GET)

```
GET /webhook?hub.mode=subscribe&hub.verify_token=mi_token_secreto_12345&hub.challenge=123
```

Meta/WhatsApp usa este endpoint para verificar que tu servidor es válido.

### 2. Recepción de Mensajes (POST)

```
POST /webhook
```

WhatsApp envía los mensajes de usuarios a este endpoint.

### 3. Listar Sesiones Activas

```
GET /whatsapp/sessions
```

Muestra todas las sesiones activas de WhatsApp con sus números de teléfono.

### 4. Eliminar Sesión

```
DELETE /whatsapp/sessions/{phone_number}
```

Elimina una sesión específica (reinicia la conversación para ese usuario).

## Configuración en Meta/WhatsApp

### Paso 1: Desplegar el servicio

```bash
# Aplicar cambios de Terraform
cd terraform
terraform apply

# O desplegar con make
make submit
gcloud run services update agent-bff-service \
  --region=us-central1 \
  --image=us-central1-docker.pkg.dev/spotgenai/agent-bff-cr/agent-bff-service:latest
```

### Paso 2: Obtener la URL del servicio

```bash
gcloud run services describe agent-bff-service \
  --region=us-central1 \
  --format='value(status.url)'
```

Ejemplo: `https://agent-bff-service-350436320279.us-central1.run.app`

### Paso 3: Configurar Webhook en Meta

1. Ve a: https://developers.facebook.com/apps
2. Selecciona tu aplicación de WhatsApp Business
3. Ve a **WhatsApp > Configuration**
4. En la sección **Webhook**, haz clic en **Edit**
5. Configura:
   - **Callback URL**: `https://tu-servicio.run.app/webhook`
   - **Verify Token**: `mi_token_secreto_12345`
6. Haz clic en **Verify and Save**
7. Suscríbete a los eventos: `messages`

### Paso 4: Probar la integración

1. Envía un mensaje de WhatsApp al número configurado
2. El agente debería responder automáticamente
3. Verifica los logs:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=agent-bff-service" \
  --limit=20 \
  --format=json
```

## Manejo de Sesiones

- Cada número de WhatsApp tiene su propia sesión con el agente
- Las sesiones se mantienen en memoria (se pierden si el servicio se reinicia)
- Para conversaciones persistentes, considera usar Cloud Firestore o Redis

## Flujo de Mensajes

1. **Usuario envía mensaje** → WhatsApp Business API
2. **WhatsApp** → POST /webhook (tu servicio)
3. **BFF Service**:
   - Extrae el mensaje y número de teléfono
   - Obtiene o crea sesión para ese usuario
   - Envía mensaje al agente de Vertex AI
4. **Vertex AI Agent** → Procesa y genera respuesta
5. **BFF Service** → Envía respuesta a WhatsApp API
6. **WhatsApp API** → Entrega mensaje al usuario

## Estructura del Payload de WhatsApp

### Mensaje entrante (POST /webhook)

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5215512345678",
          "id": "wamid.XXX",
          "timestamp": "1234567890",
          "type": "text",
          "text": {
            "body": "Hola, ¿cómo estás?"
          }
        }]
      }
    }]
  }]
}
```

### Respuesta al usuario

```json
{
  "messaging_product": "whatsapp",
  "to": "5215512345678",
  "type": "text",
  "text": {
    "body": "¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?"
  }
}
```

## Monitoreo

### Ver sesiones activas

```bash
curl https://tu-servicio.run.app/whatsapp/sessions
```

### Ver logs en tiempo real

```bash
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=agent-bff-service"
```

### Reiniciar sesión de un usuario

```bash
curl -X DELETE https://tu-servicio.run.app/whatsapp/sessions/5215512345678
```

## Consideraciones de Producción

### 1. Persistencia de Sesiones

Para producción, recomendamos almacenar sesiones en una base de datos:

```python
# Ejemplo con Firestore
from google.cloud import firestore

db = firestore.Client()

def get_or_create_whatsapp_session(user_phone: str) -> str:
    doc_ref = db.collection('whatsapp_sessions').document(user_phone)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()['session_id']
    
    # Crear nueva sesión...
    session_id = create_session()
    doc_ref.set({'session_id': session_id, 'created_at': firestore.SERVER_TIMESTAMP})
    
    return session_id
```

### 2. Rate Limiting

WhatsApp tiene límites de mensajes. Considera implementar rate limiting.

### 3. Seguridad del Token

**⚠️ IMPORTANTE**: El token de WhatsApp está actualmente en texto plano. Para producción:

1. Usa **Secret Manager**:

```bash
# Crear secret
echo -n "TU_TOKEN" | gcloud secrets create whatsapp-token --data-file=-

# Dar acceso al service account
gcloud secrets add-iam-policy-binding whatsapp-token \
  --member="serviceAccount:agent-bff-runtime@spotgenai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

2. Modifica `cloud_run.tf`:

```terraform
env {
  name = "WHATSAPP_TOKEN"
  value_source {
    secret_key_ref {
      secret  = "whatsapp-token"
      version = "latest"
    }
  }
}
```

### 4. Manejo de Errores

El código actual maneja errores básicos, pero considera:

- Reintentos exponenciales
- Dead letter queue para mensajes fallidos
- Alertas cuando el agente falla

## Debugging

### Probar webhook localmente

```bash
# Ejecutar localmente
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Usar ngrok para exponer el puerto
ngrok http 8080

# Configurar la URL de ngrok en Meta
```

### Simular mensaje de WhatsApp

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5215512345678",
            "type": "text",
            "text": {
              "body": "Hola"
            }
          }]
        }
      }]
    }]
  }'
```

## Recursos

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Webhook Setup Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)

## Soporte

Si tienes problemas:

1. Verifica que el webhook esté verificado en Meta
2. Revisa los logs de Cloud Run
3. Verifica que el token de WhatsApp sea válido
4. Confirma que el número de teléfono esté activo
