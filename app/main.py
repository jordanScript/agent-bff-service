from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from google.auth import default
from google.auth.transport.requests import Request
import logging
import requests
from typing import Dict, Optional
from google.cloud import speech_v1 as speech
from app.services.speech_service import speech_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent BFF Service",
    version="1.0.1",
    description="Backend for Frontend service para comunicación con Vertex AI Agent - CI/CD with WIF enabled"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración del agente
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "spotgenai")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")

# Configuración de WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mi_token_secreto_12345")
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Almacenamiento en memoria de sesiones por usuario de WhatsApp
whatsapp_sessions: Dict[str, str] = {}

# Obtener credenciales (se refrescarán según sea necesario)
credentials, _ = default()

# URLs de la API
BASE_API_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"

def get_auth_headers():
    """Obtiene headers con token actualizado"""
    if not credentials.valid:
        credentials.refresh(Request())
    return {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

# Modelos de datos
class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None

class QueryRequest(BaseModel):
    query: str
    context: dict | None = None

class Echo(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": os.getenv("SERVICE_NAME", "agent-bff-service"),
        "agent": {
            "project": PROJECT_ID,
            "location": LOCATION,
            "reasoning_engine_id": REASONING_ENGINE_ID
        }
    }


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.get("/ping")
def ping():
    return "pong"


@app.post("/echo")
def echo(body: Echo):
    return {"echo": body.message}


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Endpoint principal para chatear con el agente de Vertex AI.
    Usa async_stream_query para enviar mensajes en una sesión.
    """
    try:
        logger.info(f"Received chat message: {message.message[:50]}...")
        
        # Obtener headers con token actualizado
        headers = get_auth_headers()
        
        # Crear o obtener sesión
        session_id = message.session_id
        
        if not session_id:
            # Crear nueva sesión
            create_session_url = f"{BASE_API_URL}:query"
            
            payload = {
                "class_method": "async_create_session",
                "input": {
                    "user_id": "default_user"
                }
            }
            
            logger.info("Creating new session")
            session_response = requests.post(
                create_session_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Session response status: {session_response.status_code}")
            logger.info(f"Session response: {session_response.text}")
            
            session_response.raise_for_status()
            session_result = session_response.json()
            # El session_id está en output.id
            session_id = session_result.get("output", {}).get("id")
            logger.info(f"Created session: {session_id}")
        
        # Enviar mensaje usando async_stream_query
        stream_query_url = f"{BASE_API_URL}:streamQuery?alt=sse"
        
        payload = {
            "class_method": "async_stream_query",
            "input": {
                "user_id": "default_user",
                "session_id": session_id,
                "message": message.message
            }
        }
        
        logger.info(f"Sending message with session: {session_id}")
        response = requests.post(
            stream_query_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        logger.info(f"Stream query response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Received response from agent: {result}")
        
        # Extraer la respuesta del texto del modelo
        agent_response = result.get("content", {}).get("parts", [{}])[0].get("text", str(result))
        
        return ChatResponse(
            response=agent_response,
            session_id=session_id
        )
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error calling agent: {e.response.text}", exc_info=True)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error from Reasoning Engine: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with agent: {str(e)}"
        )


@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    Endpoint genérico para consultas al agente usando streamQuery.
    """
    try:
        logger.info(f"Received query: {request.query[:50]}...")
        
        # Obtener headers con token actualizado
        headers = get_auth_headers()
        
        # Preparar el input
        input_data = {"prompt": request.query}
        
        if request.context:
            input_data.update(request.context)
        
        # Preparar el payload para streamQuery usando class_method
        payload = {
            "class_method": "async_stream_query",
            "input": input_data
        }
        
        # Ejecutar la consulta usando streamQuery
        logger.info(f"Querying reasoning engine with streamQuery")
        query_url = f"{BASE_API_URL}:streamQuery"
        response = requests.post(
            query_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extraer la respuesta del formato de streaming
        if "output" in result:
            response_text = result["output"]
        else:
            response_text = result
        
        return {
            "success": True,
            "response": response_text
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error calling agent: {e.response.text}", exc_info=True)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error from Reasoning Engine: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error querying agent: {str(e)}"
        )


@app.get("/agent/info")
async def agent_info():
    """
    Obtiene información sobre el agente configurado.
    """
    return {
        "reasoning_engine_name": f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}",
        "project": PROJECT_ID,
        "location": LOCATION,
        "reasoning_engine_id": REASONING_ENGINE_ID,
        "api_base_url": BASE_API_URL,
        "available_methods": [
            "async_create_session",
            "async_search_memory",
            "async_list_sessions",
            "register_feedback"
        ]
    }


# ==================== WhatsApp Integration ====================

async def download_whatsapp_audio(audio_id: str) -> Optional[bytes]:
    """
    Descarga audio desde WhatsApp Business API.
    
    Args:
        audio_id: ID del archivo de audio en WhatsApp
        
    Returns:
        Bytes del audio o None si falla
    """
    try:
        # 1. Obtener URL del audio
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        
        media_url = f"https://graph.facebook.com/v18.0/{audio_id}"
        logger.info(f"🔍 Obteniendo URL del audio: {audio_id}")
        
        response = requests.get(media_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        audio_url = response.json().get("url")
        
        if not audio_url:
            logger.error("❌ No se obtuvo URL del audio")
            return None
        
        # 2. Descargar el audio
        logger.info(f"⬇️  Descargando audio desde: {audio_url}")
        audio_response = requests.get(audio_url, headers=headers, timeout=30)
        audio_response.raise_for_status()
        
        audio_bytes = audio_response.content
        logger.info(f"✅ Audio descargado: {len(audio_bytes)} bytes")
        
        return audio_bytes
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error de red descargando audio: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado descargando audio: {e}", exc_info=True)
        return None


def send_whatsapp_message(phone_number: str, message: str):
    """
    Envía un mensaje a través de WhatsApp Business API.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"WhatsApp message sent to {phone_number}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        raise


def get_or_create_whatsapp_session(user_phone: str) -> str:
    """
    Obtiene o crea una sesión del agente para un usuario de WhatsApp.
    """
    if user_phone in whatsapp_sessions:
        return whatsapp_sessions[user_phone]
    
    # Crear nueva sesión
    headers = get_auth_headers()
    create_session_url = f"{BASE_API_URL}:query"
    
    payload = {
        "class_method": "async_create_session",
        "input": {
            "user_id": f"whatsapp_{user_phone}"
        }
    }
    
    try:
        session_response = requests.post(
            create_session_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        session_response.raise_for_status()
        session_result = session_response.json()
        session_id = session_result.get("output", {}).get("id")
        
        # Guardar sesión
        whatsapp_sessions[user_phone] = session_id
        logger.info(f"Created WhatsApp session for {user_phone}: {session_id}")
        
        return session_id
    except Exception as e:
        logger.error(f"Error creating WhatsApp session: {str(e)}")
        raise


async def process_whatsapp_message(phone_number: str, message_text: str, is_transcription: bool = False, confidence: float = 1.0):
    """
    Procesa un mensaje de WhatsApp y obtiene respuesta del agente.
    
    Args:
        phone_number: Número de teléfono del usuario
        message_text: Texto del mensaje (puede ser texto directo o transcripción de audio)
        is_transcription: Si es True, el mensaje proviene de una transcripción de audio
        confidence: Nivel de confianza de la transcripción (0.0 a 1.0)
    """
    try:
        # Obtener o crear sesión
        session_id = get_or_create_whatsapp_session(phone_number)
        
        # Obtener headers con token actualizado
        headers = get_auth_headers()
        
        # Si es transcripción con baja confianza, agregar contexto
        if is_transcription and confidence < 0.8:
            message_text = f"[Audio transcrito - confianza {confidence:.0%}] {message_text}"
        
        # Enviar mensaje al agente
        stream_query_url = f"{BASE_API_URL}:streamQuery?alt=sse"
        
        payload = {
            "class_method": "async_stream_query",
            "input": {
                "user_id": f"whatsapp_{phone_number}",
                "session_id": session_id,
                "message": message_text
            }
        }
        
        logger.info(f"Sending WhatsApp message to agent: {message_text[:50]}...")
        response = requests.post(
            stream_query_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extraer respuesta del agente
        agent_response = result.get("content", {}).get("parts", [{}])[0].get("text", "Lo siento, no pude procesar tu mensaje.")
        
        return agent_response
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}", exc_info=True)
        return "Lo siento, ocurrió un error procesando tu mensaje. Por favor intenta de nuevo."


@app.get("/webhook")
async def verify_webhook(request: FastAPIRequest):
    """
    Verifica el webhook de WhatsApp (requerido por Meta).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"Webhook verification request: mode={mode}, token={token}")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        # WhatsApp espera el challenge como está (string o int)
        try:
            return int(challenge)
        except (ValueError, TypeError):
            return challenge
    else:
        logger.warning("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def whatsapp_webhook(request: FastAPIRequest):
    """
    Recibe mensajes de WhatsApp y los procesa con el agente.
    Soporta mensajes de texto y audio (voz).
    """
    try:
        body = await request.json()
        logger.info(f"📩 WhatsApp webhook received: {body}")
        
        # Verificar que sea un mensaje
        if body.get("object") != "whatsapp_business_account":
            return {"status": "ok"}
        
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # Procesar mensajes
                messages = value.get("messages", [])
                for message in messages:
                    # Obtener datos del mensaje
                    phone_number = message.get("from")
                    message_type = message.get("type")
                    
                    logger.info(f"📱 Mensaje de {phone_number}, tipo: {message_type}")
                    
                    # Procesar mensajes de TEXTO
                    if message_type == "text":
                        message_text = message.get("text", {}).get("body", "")
                        
                        logger.info(f"💬 Procesando mensaje de texto: {message_text[:50]}...")
                        
                        # Procesar con el agente
                        agent_response = await process_whatsapp_message(
                            phone_number, 
                            message_text
                        )
                        
                        # Enviar respuesta por WhatsApp
                        send_whatsapp_message(phone_number, agent_response)
                    
                    # Procesar mensajes de AUDIO (voz)
                    elif message_type == "audio":
                        audio_id = message.get("audio", {}).get("id")
                        
                        if not audio_id:
                            logger.error("❌ No se encontró ID de audio en el mensaje")
                            send_whatsapp_message(
                                phone_number,
                                "❌ No pude procesar el audio. Por favor, intenta de nuevo."
                            )
                            continue
                        
                        logger.info(f"🎤 Procesando mensaje de audio: {audio_id}")
                        
                        # 1. Descargar audio desde WhatsApp
                        audio_bytes = await download_whatsapp_audio(audio_id)
                        
                        if not audio_bytes:
                            send_whatsapp_message(
                                phone_number,
                                "❌ No pude descargar el audio. Por favor, intenta enviar otro mensaje de voz."
                            )
                            continue
                        
                        # 2. Transcribir con Speech-to-Text
                        logger.info(f"🎯 Transcribiendo audio de {phone_number}...")
                        transcription = speech_service.transcribe_audio(
                            audio_content=audio_bytes,
                            language_code="es-US",  # Español de Estados Unidos
                            encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                            sample_rate_hertz=16000
                        )
                        
                        if not transcription["success"]:
                            error_msg = transcription.get("error", "Error desconocido")
                            logger.error(f"❌ Error en transcripción: {error_msg}")
                            send_whatsapp_message(
                                phone_number,
                                "❌ No pude entender el audio. ¿Podrías hablar más claro o escribir tu mensaje?"
                            )
                            continue
                        
                        # 3. Extraer transcripción y confianza
                        transcript = transcription["transcript"]
                        confidence = transcription["confidence"]
                        
                        logger.info(
                            f"✅ Audio transcrito exitosamente:\n"
                            f"   Texto: '{transcript}'\n"
                            f"   Confianza: {confidence:.2%}"
                        )
                        
                        # 4. Notificar al usuario sobre la transcripción (opcional)
                        if confidence < 0.7:  # Confianza baja
                            send_whatsapp_message(
                                phone_number,
                                f"🎤 Entendí: \"{transcript}\"\n\n"
                                f"⚠️ No estoy muy seguro. ¿Es correcto?"
                            )
                        
                        # 5. Procesar transcripción con el agente
                        agent_response = await process_whatsapp_message(
                            phone_number, 
                            transcript,
                            is_transcription=True,
                            confidence=confidence
                        )
                        
                        # 6. Enviar respuesta del agente
                        send_whatsapp_message(phone_number, agent_response)
                    
                    # Otros tipos de mensaje
                    else:
                        logger.info(f"ℹ️  Tipo de mensaje no soportado: {message_type}")
                        send_whatsapp_message(
                            phone_number,
                            f"ℹ️ Solo puedo procesar mensajes de texto y audio de voz. "
                            f"Tipo recibido: {message_type}"
                        )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error procesando webhook de WhatsApp: {str(e)}", exc_info=True)
        # Siempre devolver 200 para evitar que WhatsApp reintente
        return {"status": "error", "message": str(e)}


@app.get("/whatsapp/sessions")
async def list_whatsapp_sessions():
    """
    Lista todas las sesiones activas de WhatsApp.
    """
    return {
        "total_sessions": len(whatsapp_sessions),
        "sessions": [
            {
                "phone_number": phone,
                "session_id": session_id
            }
            for phone, session_id in whatsapp_sessions.items()
        ]
    }


@app.delete("/whatsapp/sessions/{phone_number}")
async def delete_whatsapp_session(phone_number: str):
    """
    Elimina una sesión de WhatsApp (para reiniciar la conversación).
    """
    if phone_number in whatsapp_sessions:
        del whatsapp_sessions[phone_number]
        return {"status": "deleted", "phone_number": phone_number}
    else:
        raise HTTPException(status_code=404, detail="Session not found")
