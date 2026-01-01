import base64
import requests
from app.config.settings import settings
from app.utils.logger import logger


class STTService:
    """Speech-to-Text service using Deepgram REST API"""
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY if hasattr(settings, 'DEEPGRAM_API_KEY') else None
        
        if self.api_key:
            self.base_url = "https://api.deepgram.com/v1/listen"
            logger.info("✅ STT service initialized (Deepgram)")
        else:
            self.base_url = None
            logger.warning("⚠️  DEEPGRAM_API_KEY not found - STT will not work")
    
    async def transcribe_audio(self, audio_base64: str, mime_type: str) -> str:
        """
        Transcribe audio to text using Deepgram
        
        Args:
            audio_base64: Base64 encoded audio data
            mime_type: Audio MIME type (e.g., "audio/webm")
        
        Returns:
            Transcribed text
        """
        if not self.api_key:
            return "Audio transcription is not available. Please configure DEEPGRAM_API_KEY."
        
        try:
            # Decode base64 audio to binary
            audio_data = base64.b64decode(audio_base64)
            
            # Headers
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": mime_type
            }
            
            # Query parameters
            params = {
                "model": "nova-3",
                "language": "en",
                "smart_format": "true",
                "punctuate": "true"
            }
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers=headers,
                params=params,
                data=audio_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract transcript
                transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                confidence = result['results']['channels'][0]['alternatives'][0]['confidence']
                
                logger.info(f"Transcription successful (confidence: {confidence:.2f})")
                return transcript
            else:
                error_msg = f"Deepgram API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"Transcription failed: {error_msg}"
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"Transcription failed: {str(e)}"


# Singleton instance
stt_service = STTService()
