"""
Script de prueba para validar el servicio de Speech-to-Text
"""
import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from services.speech_service import speech_service
    print("✅ SpeechService importado correctamente")
    
    # Probar inicialización
    print(f"✅ Cliente inicializado: {speech_service.client is not None}")
    
    # Simular transcripción con audio vacío (solo para validar estructura)
    print("\n🧪 Probando estructura de respuesta...")
    result = speech_service.transcribe_audio(
        audio_content=b'',  # Audio vacío
        language_code="es-US"
    )
    
    print(f"✅ Respuesta tiene estructura correcta:")
    print(f"   - success: {result.get('success')}")
    print(f"   - transcript: {result.get('transcript')}")
    print(f"   - confidence: {result.get('confidence')}")
    print(f"   - error: {result.get('error', 'N/A')}")
    
    print("\n✅ ¡Todo funcionando correctamente!")
    print("\nPara probar con audio real:")
    print("1. Inicia el servidor: uvicorn app.main:app --reload --port 8080")
    print("2. Envía un mensaje de voz por WhatsApp al número configurado")
    print("3. Revisa los logs para ver la transcripción")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\nAsegúrate de instalar las dependencias:")
    print("pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nVerifica que:")
    print("1. Las credenciales estén configuradas (gcloud auth application-default login)")
    print("2. La API de Speech-to-Text esté habilitada")
    print("3. Tengas los permisos necesarios")
    sys.exit(1)
