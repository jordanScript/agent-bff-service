from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from google.auth import default
from google.auth.transport.requests import Request
import logging
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent BFF Service",
    version="1.0.0",
    description="Backend for Frontend service para comunicación con Vertex AI Agent"
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
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "5664318868441530368")

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
    Endpoint genérico para consultas al agente con contexto adicional.
    """
    try:
        logger.info(f"Received query: {request.query[:50]}...")
        
        # Obtener headers con token actualizado
        headers = get_auth_headers()
        
        # Preparar el input
        input_data = {"prompt": request.query}
        
        if request.context:
            input_data.update(request.context)
        
        # Preparar el payload
        payload = {"input": input_data}
        
        # Ejecutar la consulta
        logger.info(f"Querying reasoning engine with context")
        query_url = f"{BASE_API_URL}:query"
        response = requests.post(
            query_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "response": result
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
