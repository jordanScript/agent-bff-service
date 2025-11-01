#!/bin/bash
# Script de prueba para el agente en Vertex AI

PROJECT_ID="spotgenai"
LOCATION="us-central1"
REASONING_ENGINE_ID="5664318868441530368"

# Obtener token
TOKEN=$(gcloud auth print-access-token)

BASE_URL="https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${REASONING_ENGINE_ID}"

echo "=== Test 1: Crear sesión ==="
SESSION_RESPONSE=$(curl -s -X POST "${BASE_URL}:async_create_session" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "class_method": "async_create_session",
    "input": {
      "user_id": "u_123"
    }
  }')

echo "$SESSION_RESPONSE" | jq .

# Extraer session_id si existe
SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.session_id // empty')

if [ -n "$SESSION_ID" ]; then
  echo -e "\n=== Test 2: Buscar en memoria con sesión: $SESSION_ID ==="
  curl -s -X POST "${BASE_URL}:async_search_memory" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"class_method\": \"async_search_memory\",
      \"input\": {
        \"session_id\": \"${SESSION_ID}\",
        \"query\": \"Hola, ¿cómo estás?\"
      }
    }" | jq .
else
  echo "No se pudo crear la sesión"
fi
