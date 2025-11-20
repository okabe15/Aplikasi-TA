"""
Enhanced TTS Service with Clean Text Support
Integrated with existing backend structure
"""

import edge_tts
import io
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TTSService:
    """
    Enhanced TTS Service with clean text processing
    Maintains compatibility with existing code
    """
    
    # Available voices for different styles
    VOICES = {
        "classic": "en-GB-RyanNeural",      # British male for classic text
        "modern": "en-US-GuyNeural",        # American male for modern text
        "narrator": "en-US-AriaNeural",     # Female narrator voice
        "male": "en-US-DavisNeural",        # Male voice
        "female": "en-US-JennyNeural",      # Female voice
    }
    
    def clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for better TTS output
        Removes markdown, XML tags, and other artifacts
        
        This is THE KEY FUNCTION that fixes the "asterisk asterisk" problem!
        """
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Step 1: Remove markdown formatting FIRST (this is crucial!)
        # **Watson:** becomes Watson:
        cleaned = re.sub(r'\*\*([^*]+):\*\*', r'\1:', cleaned)
        # **text** becomes text
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        # *text* becomes text
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
        # _text_ becomes text
        cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
        
        # Step 2: Remove XML/HTML tags
        cleaned = re.sub(r'<[^>]*>', '', cleaned)
        
        # Step 3: Handle HTML entities
        cleaned = cleaned.replace('&quot;', '"')
        cleaned = cleaned.replace('&apos;', "'")
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')
        cleaned = cleaned.replace('&amp;', '&')
        
        # Step 4: Clean whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Step 5: Remove enclosing quotes if they wrap the whole text
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        return cleaned
    
    async def generate_audio(
        self, 
        text: str, 
        voice_type: str = "modern",
        rate: str = "medium",
        pitch: str = "medium",
        use_ssml: bool = False
    ) -> Optional[bytes]:
        """
        Generate TTS audio using edge-tts
        Now with automatic text cleaning!
        
        Args:
            text: Text to synthesize (will be cleaned automatically)
            voice_type: Voice type (classic, modern, narrator, male, female)
            rate: Speech rate (slow, medium, fast)
            pitch: Voice pitch (low, medium, high)
            use_ssml: Use SSML formatting (not recommended for clean audio)
        
        Returns:
            Audio data as bytes, or None if generation fails
        """
        try:
            # Validate voice type
            if voice_type not in self.VOICES:
                logger.warning(f"Unknown voice type '{voice_type}', using 'modern'")
                voice_type = "modern"
            
            voice = self.VOICES[voice_type]
            
            # 🔥 KEY CHANGE: Automatically clean the text!
            cleaned_text = self.clean_text_for_tts(text)
            
            logger.info(f"Original text: '{text[:50]}...'")
            logger.info(f"Cleaned text: '{cleaned_text[:50]}...'")
            
            # Skip if no valid text
            if not cleaned_text or cleaned_text.lower() == "none":
                logger.warning("No valid text to synthesize after cleaning")
                return None
            
            # Prepare final text
            if use_ssml:
                # Rate mapping
                rate_values = {"slow": "-20%", "medium": "+0%", "fast": "+20%"}
                rate_setting = rate_values.get(rate, "+0%")
                
                # Pitch mapping
                pitch_values = {"low": "-10Hz", "medium": "+0Hz", "high": "+10Hz"}
                pitch_setting = pitch_values.get(pitch, "+0Hz")
                
                # Create SSML
                final_text = f"""
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <prosody rate="{rate_setting}" pitch="{pitch_setting}">
                        {cleaned_text}
                    </prosody>
                </speak>
                """
                logger.info(f"Using SSML with rate={rate_setting}, pitch={pitch_setting}")
            else:
                # Use plain text - this is better for natural dialogue and narration
                final_text = cleaned_text
                logger.info("Using plain text (recommended for clean audio)")
            
            # Create edge-tts communicate object
            communicate = edge_tts.Communicate(final_text, voice)
            
            # Collect audio into a BytesIO buffer
            audio_stream = io.BytesIO()
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
            
            # Rewind for reading
            audio_stream.seek(0)
            audio_bytes = audio_stream.read()
            
            if len(audio_bytes) == 0:
                logger.error("Generated empty audio")
                return None
            
            logger.info(
                f"✅ TTS Success: Generated {len(audio_bytes)} bytes "
                f"for voice={voice_type} (voice={voice})"
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ TTS generation error: {str(e)}", exc_info=True)
            return None
    
    def get_available_voices(self) -> dict:
        """Get list of available voices"""
        return {
            "voices": self.VOICES,
            "voice_types": list(self.VOICES.keys()),
            "description": {
                "modern": "Modern American male voice - clear and natural",
                "classic": "British male voice - perfect for classic literature",
                "narrator": "American female narrator - warm and engaging",
                "male": "American male voice - versatile and clear",
                "female": "American female voice - friendly and expressive"
            }
        }

# Global instance
tts_service = TTSService()