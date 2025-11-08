"""Servicio para transcripción de audio usando Google Cloud Speech-to-Text"""

import logging
from typing import Dict, Any, Optional
from google.cloud import speech_v1 as speech
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class SpeechService:
    """Servicio para convertir audio a texto usando Google Cloud Speech-to-Text"""
    
    def __init__(self):
        """Inicializa el cliente de Speech-to-Text"""
        try:
            self.client = speech.SpeechClient()
            logger.info("✅ Speech-to-Text client inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al inicializar Speech-to-Text client: {e}")
            raise
    
    def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: str = "es-US",
        encoding: speech.RecognitionConfig.AudioEncoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz: int = 16000
    ) -> Dict[str, Any]:
        """
        Transcribe audio a texto usando Google Cloud Speech-to-Text.
        
        Args:
            audio_content: Contenido del audio en bytes
            language_code: Código de idioma (es-US, es-MX, en-US, etc.)
            encoding: Formato del audio (OGG_OPUS para WhatsApp)
            sample_rate_hertz: Sample rate del audio (16000 Hz para WhatsApp)
            
        Returns:
            Dict con la transcripción y metadata:
            {
                "success": bool,
                "transcript": str,
                "confidence": float,
                "language": str,
                "error": str (opcional)
            }
        """
        try:
            # Validar que hay contenido
            if not audio_content or len(audio_content) == 0:
                logger.error("Audio content vacío")
                return {
                    "success": False,
                    "transcript": "",
                    "confidence": 0.0,
                    "error": "Audio vacío"
                }
            
            # Configurar el audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Configurar la transcripción
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                # Características avanzadas
                enable_automatic_punctuation=True,  # Puntuación automática
                enable_word_time_offsets=False,     # No necesitamos timestamps
                model="default",  # Modelo por defecto
                use_enhanced=True  # Usar modelo mejorado si está disponible
            )
            
            # Realizar la transcripción
            logger.info(f"🎤 Transcribiendo audio ({len(audio_content)} bytes, idioma: {language_code})...")
            response = self.client.recognize(config=config, audio=audio)
            
            # Procesar resultados
            if not response.results:
                logger.warning("⚠️  No se obtuvieron resultados de la transcripción")
                return {
                    "success": False,
                    "transcript": "",
                    "confidence": 0.0,
                    "error": "No se pudo transcribir el audio. El audio puede estar en silencio o ser ininteligible."
                }
            
            # Obtener la mejor transcripción
            result = response.results[0]
            alternative = result.alternatives[0]
            
            transcript = alternative.transcript
            confidence = alternative.confidence
            
            logger.info(
                f"✅ Transcripción exitosa: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}' "
                f"(confianza: {confidence:.2%})"
            )
            
            return {
                "success": True,
                "transcript": transcript,
                "confidence": confidence,
                "language": language_code
            }
            
        except GoogleAPIError as e:
            logger.error(f"❌ Error de Google API al transcribir: {e}")
            return {
                "success": False,
                "transcript": "",
                "confidence": 0.0,
                "error": f"Error de API: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Error inesperado al transcribir: {e}", exc_info=True)
            return {
                "success": False,
                "transcript": "",
                "confidence": 0.0,
                "error": f"Error: {str(e)}"
            }
    
    def transcribe_audio_async(
        self,
        gcs_uri: str,
        language_code: str = "es-US"
    ) -> Dict[str, Any]:
        """
        Transcribe audio largo desde Google Cloud Storage (para audios >1 minuto).
        
        Args:
            gcs_uri: URI del audio en GCS (gs://bucket/file.ogg)
            language_code: Código de idioma
            
        Returns:
            Dict con la transcripción y metadata
        """
        try:
            audio = speech.RecognitionAudio(uri=gcs_uri)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                use_enhanced=True
            )
            
            # Operación asíncrona
            operation = self.client.long_running_recognize(
                config=config, 
                audio=audio
            )
            
            logger.info(f"⏳ Esperando transcripción asíncrona de {gcs_uri}...")
            response = operation.result(timeout=300)  # 5 min timeout
            
            if not response.results:
                return {
                    "success": False,
                    "transcript": "",
                    "confidence": 0.0,
                    "error": "No se pudo transcribir el audio largo"
                }
            
            # Combinar todos los resultados
            transcript = " ".join([
                result.alternatives[0].transcript 
                for result in response.results
            ])
            
            # Calcular confianza promedio
            confidences = [
                result.alternatives[0].confidence 
                for result in response.results
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"✅ Transcripción asíncrona completada (confianza: {avg_confidence:.2%})")
            
            return {
                "success": True,
                "transcript": transcript,
                "confidence": avg_confidence,
                "language": language_code
            }
            
        except Exception as e:
            logger.error(f"❌ Error en transcripción asíncrona: {e}", exc_info=True)
            return {
                "success": False,
                "transcript": "",
                "confidence": 0.0,
                "error": str(e)
            }


# Instancia global del servicio
speech_service = SpeechService()
