import httpx
from app.config import settings
from typing import List, Dict, Any
from app.models.schemas import ComicPanel
import json
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.ai_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    # ✅ NEW METHOD 1: Extract Characters
    async def extract_characters_from_text(self, classic_text: str, modern_text: str) -> List[Dict[str, Any]]:
        """Extract and describe main characters once for consistency"""
        
        extraction_prompt = f"""
Analyze this story excerpt and identify the main characters (maximum 5 most important).
For each character, provide a DETAILED physical description for visual consistency.

Classic Text:
{classic_text[:800]}

Modern Text:
{modern_text[:800]}

Return ONLY valid JSON:
{{
  "characters": [
    {{
      "name": "Full Character Name",
      "role": "protagonist/antagonist/supporting",
      "description": "DETAILED visual: exact height, build, facial features, hair color and style, eye color, age, typical clothing, distinguishing marks, posture, typical expression"
    }}
  ]
}}

Be extremely detailed and specific. This will be used for ALL images.
"""
        
        try:
            logger.info("🎭 Extracting characters...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a character analyst. Return only valid JSON."},
                            {"role": "user", "content": extraction_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500
                    }
                )
                
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                
                # Clean JSON
                if content.startswith('```'):
                    content = content.replace('```json', '').replace('```', '').strip()
                
                characters_data = json.loads(content)
                characters = characters_data.get('characters', [])

                 # ✅ Auto-generate IDs if missing
            for idx, char in enumerate(characters):
                if 'id' not in char or not char['id']:
                    char['id'] = char['name'].lower().replace(' ', '_').replace('.', '')
                    logger.warning(f"⚠️ Auto-generated ID: {char['id']}")
            
            logger.info(f"✅ Extracted {len(characters)} characters:")
            for char in characters:
                logger.info(f"   [{char['id']}] {char['name']}")
                
                logger.info(f"✅ Extracted {len(characters)} characters")
                for char in characters:
                    logger.info(f"   - {char['name']} ({char.get('role', 'character')})")
                
                return characters
                
        except Exception as e:
            logger.error(f"❌ Character extraction failed: {e}")
            logger.warning("⚠️ Continuing without character consistency")
            return []
    
    # ✅ NEW METHOD 2: Build Character Reference
    def build_character_reference(self, characters: List[Dict[str, Any]]) -> str:
        """Build character consistency instruction"""
    
        if not characters:
            return ""
    
        reference = "🎭 CHARACTER CONSISTENCY - USE EXACT DESCRIPTIONS:\n\n"
    
        for char in characters:
            reference += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[{char['id']}] {char['name']} ({char.get('role', 'character')}):
{char['description']}

⚠️ CRITICAL: Use this EXACT appearance in EVERY panel featuring {char['name']}.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
        return reference
    
    async def modernize_text(self, classic_text: str, temperature: float = 0.7) -> str:
        """Convert classic English to modern English"""
        
        system_message = """You are an expert literary translator specializing in modernizing classic English texts while preserving their original meaning, tone, and literary quality.

Your task:
1. Convert archaic language to modern English
2. Update outdated grammar and sentence structures  
3. Replace obsolete words with contemporary equivalents
4. Maintain the original meaning and emotional impact
5. Preserve the author's style and voice
6. Keep the text length approximately the same

Guidelines:
- Convert "thou/thee/thy" to modern pronouns
- Update verb conjugations (dost → do, hath → has)
- Replace archaic words with modern equivalents
- Simplify overly complex sentence structures
- Maintain formality level appropriate to the original
- Preserve any dialogue structure and narrative flow

Return ONLY the modernized text, no explanations."""

        user_prompt = f"Modernize this classic English text to contemporary English:\n\n{classic_text}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "E-Learning Comics Module Creator"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": 3000
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"].strip()
    
    # ✅ UPDATED: Add character parameters
    async def generate_comic_script(
        self, 
        classic_text: str,
        modern_text: str, 
        temperature: float = 0.7
    ) -> dict:
        """Generate comic script with character consistency"""
        
        try:
            # ✅ STEP 1: Extract characters FIRST
            logger.info("🎭 Step 1: Extracting characters...")
            characters = await self.extract_characters_from_text(classic_text, modern_text)
            
            # ✅ STEP 2: Build character reference
            character_reference = self.build_character_reference(characters)
            
            logger.info(f"📝 Step 2: Generating comic script with {len(characters)} characters...")
            
            system_message = f"""You are an expert comic book writer and visual storyteller. Create a detailed comic script with SEPARATED dialogue and narration components.

{character_reference}

Create comic script with:
- Character descriptions from reference above
- EXACT appearance in every panel


Create a comic script that includes:
1. 4-6 panel breakdown with detailed visual descriptions
2. Separate DIALOGUE and NARRATION for each panel
3. Visual composition and camera angles
4. Setting and atmosphere details
5. Action descriptions and character expressions

CRITICAL CHARACTER RULES:
- Use the EXACT character descriptions provided above in EVERY panel
- Do not change character appearance, clothing, or features between panels
- Maintain perfect visual consistency for all characters

Format each panel EXACTLY as follows:

**Panel [X]:**
**DIALOGUE:** [Character speech or "None"]
**NARRATION:** [Detailed story description, scene setting, character thoughts - 3-5 sentences]
**VISUAL:** [Detailed scene description WITH character descriptions from reference above]
**SETTING:** [Background/environment details]
**MOOD:** [Atmosphere and lighting]
**COMPOSITION:** [Camera angle like "medium shot", "close-up", "wide shot"]

CRITICAL RULES:
- DIALOGUE should be actual spoken words by characters - CREATE MORE DIALOGUE content from the source text
- NARRATION should be DETAILED and RICH, describing what's happening, scene context, character thoughts, and emotions (3-5 sentences per panel)
- Expand DIALOGUE to include more conversations and character interactions (2-3 sentences per panel when dialogue exists)
- Make NARRATION comprehensive to fully capture the essence and details of the modernized text
- Include character internal thoughts, environmental details, and atmospheric descriptions in narration
- Make the script suitable for western comic book style
- Ensure text is clean and suitable for speech synthesis
- ALWAYS reference the character descriptions when describing visual scenes

Example format:
**Panel 1:**
**DIALOGUE:** "You are more beautiful than a summer's day, my lady."
**NARRATION:** A noble knight approaches a fair maiden in a blooming garden, his eyes filled with admiration.
**VISUAL:** [Character name from reference]: [exact description], approaching a beautiful lady in an elegant dress
**SETTING:** Royal garden with blooming roses and stone pathways
**MOOD:** Romantic, warm golden sunlight
**COMPOSITION:** Medium shot showing both characters"""

            user_prompt = f"""Convert this text into a detailed comic script with separated dialogue and narration for each panel:

CLASSIC TEXT:
{classic_text[:1000]}

MODERN TEXT:
{modern_text}

Create 4-6 engaging panels with:
- RICH, DETAILED narration (3-5 sentences per panel)
- EXPANDED dialogue with meaningful interactions (2-3 sentences when characters speak)
- Clear visual scenes USING character descriptions from the reference
- Comprehensive descriptions for speech synthesis
- Perfect character consistency using the descriptions provided above"""
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "E-Learning Comics Script Generator"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 3000
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                script_text = data["choices"][0]["message"]["content"].strip()
                
                # ✅ RETURN WITH CHARACTERS
                return {
                    'script': script_text,
                    'characters': characters
                }
                
        except Exception as e:
            logger.error(f"Comic script generation failed: {e}", exc_info=True)
            raise
    
    def parse_comic_script(self, script_text: str) -> List[ComicPanel]:
        """Parse AI-generated comic script into structured panels"""
        import re
        
        panels = []
        panel_regex = r"\*\*Panel\s*(\d+):\*\*\s*([\s\S]*?)(?=\*\*Panel\s*\d+:\*\*|$)"
        
        matches = re.finditer(panel_regex, script_text, re.IGNORECASE)
        
        for match in matches:
            panel_num = int(match.group(1))
            panel_content = match.group(2).strip()
            
            def extract_field(content: str, field_name: str) -> str:
                pattern = rf"\*\*{field_name}:\*\*\s*([^\n]*(?:\n(?!\s*\*\*)[^\n]*)*)"
                match = re.search(pattern, content, re.IGNORECASE)
                return match.group(1).strip() if match else ""
            
            panel = ComicPanel(
                id=panel_num,
                dialogue=extract_field(panel_content, "DIALOGUE") or "None",
                narration=extract_field(panel_content, "NARRATION") or "",
                visual=extract_field(panel_content, "VISUAL") or "",
                setting=extract_field(panel_content, "SETTING") or "",
                mood=extract_field(panel_content, "MOOD") or "",
                composition=extract_field(panel_content, "COMPOSITION") or "medium shot"
            )
            
            panels.append(panel)
        
        return panels

ai_service = AIService()