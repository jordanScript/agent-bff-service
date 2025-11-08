#!/bin/bash
# Script para probar la transcripción de audio

echo "🧪 Script de prueba de Speech-to-Text"
echo "======================================"
echo ""

# Verificar que la API de Speech está habilitada
echo "1️⃣ Verificando API de Speech-to-Text..."
gcloud services list --enabled --project=spotgenai | grep speech.googleapis.com

if [ $? -eq 0 ]; then
    echo "✅ API de Speech-to-Text habilitada"
else
    echo "❌ API de Speech-to-Text NO habilitada"
    echo ""
    echo "Para habilitar, ejecuta:"
    echo "gcloud services enable speech.googleapis.com --project=spotgenai"
    exit 1
fi

echo ""
echo "2️⃣ Verificando permisos IAM..."
USER_EMAIL=$(gcloud config get-value account)
echo "Usuario activo: $USER_EMAIL"

# Verificar que el usuario tiene permisos
gcloud projects get-iam-policy spotgenai \
  --flatten="bindings[].members" \
  --filter="bindings.members:$USER_EMAIL AND bindings.role:roles/speech.client" \
  --format="table(bindings.role)"

echo ""
echo "3️⃣ Verificando credenciales..."
if [ -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo "✅ Credenciales ADC encontradas"
else
    echo "⚠️  Credenciales ADC no encontradas"
    echo ""
    echo "Para configurar, ejecuta:"
    echo "gcloud auth application-default login"
fi

echo ""
echo "4️⃣ Instalando dependencias..."
cd /home/jordan/Desktop/AGENTS/agent-bff-service
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas"
else
    echo "❌ Error instalando dependencias"
    exit 1
fi

echo ""
echo "✅ Todo listo para usar Speech-to-Text"
echo ""
echo "Para probar el servicio localmente:"
echo "  cd /home/jordan/Desktop/AGENTS/agent-bff-service"
echo "  uvicorn app.main:app --reload --port 8080"
echo ""
echo "Para probar con un audio de WhatsApp, envía un mensaje de voz al número configurado."
