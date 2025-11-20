import httpx
from app.config import settings
from app.models.schemas import Exercise, TrainingRequest
from typing import List, Dict, Any  # ✅ ADD Dict, Any
import json
import uuid
import logging
import re
import os

logger = logging.getLogger(__name__)

class TrainingService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.ai_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.grammar_dir = "grammar_topics"

    GRAMMAR_TOPICS = [
        {"id": "tenses", "label": "Tenses", "description": "Present, Past, Perfect forms", "is_basic": True},
        {"id": "modals", "label": "Modal Verbs", "description": "can, must, should, etc.", "is_basic": False},
        {"id": "articles", "label": "Articles", "description": "a, an, the usage", "is_basic": True},
        {"id": "pronouns", "label": "Pronouns", "description": "thou/you, thy/your, etc.", "is_basic": True},
        {"id": "passive", "label": "Passive Voice", "description": "Active to passive conversion", "is_basic": False},
        {"id": "conditionals", "label": "Conditionals", "description": "If clauses and hypotheticals", "is_basic": False},
        {"id": "vocabulary", "label": "Vocabulary", "description": "Archaic to modern word changes", "is_basic": True},
        {"id": "syntax", "label": "Sentence Structure", "description": "Word order and syntax", "is_basic": False},
        {"id": "pronunciation", "label": "Pronunciation", "description": "Classic vs modern pronunciation", "is_basic": True}
    ]

    # ✅ TAMBAH METHOD 1 DI SINI (COPY-PASTE)
    async def extract_characters_from_text(self, classic_text: str, modern_text: str) -> List[Dict[str, Any]]:
        """Extract and describe main characters once for consistency"""
        
        extraction_prompt = f"""
Analyze this story excerpt and identify the main characters (maximum 5 most important).
For each character, provide a DETAILED physical description that will be used consistently across all comic panels.

Classic Text:
{classic_text[:800]}

Modern Text:
{modern_text[:800]}

Return ONLY valid JSON in this exact format:
{{
  "characters": [
    {{
      "name": "Full Character Name",
      "role": "protagonist/antagonist/supporting",
      "description": "DETAILED visual description including: exact height, build, facial features, hair color and style, eye color, age, typical clothing, distinguishing marks, posture, typical expression"
    }}
  ]
}}

Be extremely detailed and specific. This description will be used for ALL images to maintain consistency.
"""
        
        try:
            logger.info("🎭 Extracting characters from text...")
            
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
                            {"role": "system", "content": "You are a character analysis expert. Return only valid JSON."},
                            {"role": "user", "content": extraction_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500
                    }
                )
                
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                
                # Clean JSON
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                characters_data = json.loads(content)
                characters = characters_data.get('characters', [])
                
                logger.info(f"✅ Extracted {len(characters)} characters")
                return characters
                
        except Exception as e:
            logger.error(f"❌ Character extraction failed: {e}")
            return []

    # ✅ TAMBAH METHOD 2 DI SINI (COPY-PASTE)
    def build_character_reference(self, characters: List[Dict[str, Any]]) -> str:
        """Build character consistency instruction for AI"""
        
        if not characters:
            return ""
        
        reference = "🎭 CHARACTER CONSISTENCY - USE EXACT DESCRIPTIONS:\n\n"
        
        for char in characters:
            reference += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{char['name']} ({char.get('role', 'character')}):
{char['description']}

⚠️ CRITICAL: Use this EXACT appearance in EVERY panel featuring {char['name']}.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        return reference


    # ✅ NEW: Markdown parser sebagai fallback
    def parse_markdown_exercises(self, markdown_text: str, num_questions: int) -> List[dict]:
        """Parse exercises from markdown format when AI returns text instead of JSON"""
        exercises = []
        
        # Split by question sections
        question_blocks = re.split(r'###\s*\*\*Question\s+\d+:', markdown_text)
        
        for idx, block in enumerate(question_blocks[1:], 1):
            if idx > num_questions:
                break
                
            try:
                # Extract question text
                question_match = re.search(r'\*\*Question:\*\*\s*\n(.+?)(?=\n\*\*|\n[A-D]\.)', block, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else ''
                
                # Extract classic/modern text
                classic_match = re.search(r'\*\*ClassicText:\*\*\s*\n"?(.+?)"?(?=\n\*\*)', block, re.DOTALL)
                modern_match = re.search(r'\*\*ModernText:\*\*\s*\n"?(.+?)"?(?=\n\*\*)', block, re.DOTALL)
                
                classic_text = classic_match.group(1).strip() if classic_match else None
                modern_text = modern_match.group(1).strip() if modern_match else None
                
                # Extract comic reference
                comic_ref_match = re.search(r'\*\*Comic Context:\*\*\s*\n(.+?)(?=\n\*\*)', block, re.DOTALL)
                comic_reference = comic_ref_match.group(1).strip() if comic_ref_match else None
                
                # Extract options
                options = []
                option_matches = re.findall(r'^([A-D])\.\s+(.+?)$', block, re.MULTILINE)
                options = [opt[1].strip() for opt in option_matches]
                
                # Extract correct answer
                correct_match = re.search(r'\*\*Correct Answer:\*\*\s*\n([A-D])\.', block)
                if correct_match:
                    correct_letter = correct_match.group(1)
                    correct_index = ord(correct_letter) - ord('A')
                else:
                    correct_index = 0
                
                # Extract explanation
                explanation_match = re.search(r'\*\*Explanation:\*\*\s*\n(.+?)(?=\n---|\n###|$)', block, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else ''
                
                # Extract grammar rule
                grammar_match = re.search(r'(Present Perfect|Past Simple|Future Simple|Modal Verb|Article|Pronoun|Passive Voice|Conditional)', explanation)
                grammar_rule = grammar_match.group(1) if grammar_match else None
                
                # Build exercise object
                exercise = {
                    'type': 'grammar',
                    'question': question_text,
                    'options': options,
                    'correct': correct_index,
                    'explanation': explanation
                }
                
                if classic_text:
                    exercise['classicText'] = classic_text
                if modern_text:
                    exercise['modernText'] = modern_text
                if comic_reference:
                    exercise['comicReference'] = comic_reference
                if grammar_rule:
                    exercise['grammarRule'] = grammar_rule
                
                exercises.append(exercise)
                
            except Exception as parse_error:
                logger.warning(f"Failed to parse question {idx}: {parse_error}")
                continue
        
        logger.info(f"✅ Parsed {len(exercises)} exercises from markdown")
        return exercises

    async def generate_training_exercises(self, request: TrainingRequest) -> Dict[str, Any]:  # ✅ CHANGE THIS
        """Generate training exercises based on comic content + grammar reference hybrid"""

        # Extract characters FIRST
        characters = await self.extract_characters_from_text(
            request.classic_text, 
            request.modern_text
        )
        character_reference = self.build_character_reference(characters)

        # 1️⃣ Ambil deskripsi topik dari daftar di atas
        topic_descriptions = [
            f"{topic['label']}: {topic['description']}"
            for topic in self.GRAMMAR_TOPICS
            if topic['id'] in request.selected_topics
        ]

        # 2️⃣ Ambil referensi grammar manual dari file teks
        context_from_files = []
        for topic_id in request.selected_topics:
            file_path = os.path.join(self.grammar_dir, f"{topic_id}.txt")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            context_from_files.append(f"### {topic_id.upper()} ###\n{content}")
                except Exception as e:
                    logger.warning(f"Gagal membaca file {file_path}: {e}")
            else:
                logger.info(f"Tidak ada file grammar untuk topik: {topic_id}")

        grammar_reference_text = "\n\n".join(context_from_files) if context_from_files else "(No manual grammar reference found.)"

        # 3️⃣ Siapkan system message dengan RAG instruction yang lebih kuat
        system_message = f"""
You are an expert English teacher and content creator specializing in grammar instruction.

{character_reference}

## 📚 YOUR TASK: RAG-BASED QUESTION GENERATION

Below, you will find GRAMMAR ARCHETYPES (question templates and patterns). These are NOT just examples - they are STRUCTURED TEMPLATES that you MUST follow.

### HOW TO USE THE ARCHETYPES:

1. **READ each archetype carefully** - Each archetype has:
   - An "Instruction for AI" telling you how to create that type of question
   - An example format showing the structure
   - Grammar rules to apply

2. **FOLLOW the archetype structure exactly**:
   - Use the same question pattern (Fill in blank? Transformation? Identification?)
   - Match the format (what fields to include)
   - Apply the grammar rule shown in the archetype

3. **ADAPT to the comic content**:
   - Replace archetype examples with actual dialogue/narration/setting from the comic panels below
   - Keep character names, places, and events from the comic
   - Ensure questions feel natural in the comic's world

4. **MIX archetype types**:
   - Use different archetypes (don't repeat the same pattern)
   - Vary question types across the requested topics
   - Distribute difficulty levels appropriately

### DIFFICULTY GUIDELINES:
- **"beginner"**: Simple vocabulary, basic tenses (present/past), articles, basic pronouns, straightforward transformations
- **"medium"**: Modal verbs, compound sentences, passive voice basics, intermediate vocabulary, nuanced meanings
- **"advanced"**: Complex conditionals, advanced passive voice, syntax changes, idiomatic expressions, subtle distinctions

### QUESTION SOURCE REQUIREMENTS:
Generate questions from ALL these sources (mix equally):
1. **Dialogue-based**: Character speech and conversations
2. **Narration-based**: Story narration text and descriptions
3. **Setting-based**: Location descriptions, mood, atmosphere, visual context

---
## 📖 GRAMMAR ARCHETYPES (YOUR TEMPLATES)
{grammar_reference_text}
---

### OUTPUT FORMAT:
Return ONLY a valid JSON array. No markdown code blocks, no explanations, no preamble.

[
  {{
    "type": "multiple_choice",
    "difficulty": "beginner|medium|advanced",
    "question": "Question following an archetype pattern, adapted to comic context",
    "classic_text": "Direct quote from classic text if relevant",
    "modern_text": "Modern translation if relevant",
    "comic_reference": "Panel X: Specific dialogue/narration/setting detail",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0,
    "explanation": "Clear explanation citing the grammar rule from archetype",
    "grammar_rule": "Specific rule name from archetype"
  }}
]

CRITICAL RULES:
✅ Follow archetype structures - don't invent random questions
✅ Use actual comic content (dialogue, narration, settings from panels below)
✅ Match archetype difficulty guidance
✅ Include grammar_rule field matching the archetype
✅ Return ONLY valid JSON (no markdown, no extra text)
"""

        # 4️⃣ Format isi komik & teks input - INCLUDE SETTING & MOOD
        panels_text = "\n\n".join([
            f"Panel {panel.id}:\n- Dialogue: \"{panel.dialogue}\"\n- Narration: {panel.narration}\n- Setting: {panel.setting}\n- Mood: {panel.mood}\n- Visual: {panel.visual}"
            for panel in request.panels
        ])

        # ✅ Generate MORE questions - increase by 50%
        total_questions = max(request.num_questions, 15)  # Minimum 15 questions
        beginner_count = int(total_questions * 0.4)  # 40% beginner
        medium_count = int(total_questions * 0.35)   # 35% medium
        advanced_count = total_questions - beginner_count - medium_count  # 25% advanced

        user_prompt = f"""
Create {total_questions} grammar-based questions with the following difficulty distribution:
- {beginner_count} BEGINNER level questions
- {medium_count} MEDIUM level questions
- {advanced_count} ADVANCED level questions

Base your questions on ALL these sources (distribute equally):
1. Character dialogues from panels
2. Narration text from panels
3. Setting descriptions and mood/atmosphere

CLASSIC TEXT:
{request.classic_text[:1000]}

MODERN TEXT:
{request.modern_text[:1000]}

COMIC PANELS (with dialogues, narrations, settings, and moods):
{panels_text}

FOCUS TOPICS: {', '.join(topic_descriptions)}

IMPORTANT:
- Create a MIX of questions from dialogue, narration, AND setting descriptions
- Ensure each difficulty level is accurately classified
- Use the grammar reference for correctness, but all content must come from the comic
- Make questions engaging and contextual to the story
"""

        # 5️⃣ Panggil API model AI (DeepSeek, GPT, dll.)
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Comic Grammar Generator"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            )

        # 6️⃣ Validasi dan parsing respons model
        if not response.is_success:
            raise RuntimeError(f"OpenRouter API error {response.status_code}: {response.text}")

        data = response.json()
        if "choices" not in data or not data["choices"]:
            raise RuntimeError(f"OpenRouter API response tidak punya 'choices': {data}")

        response_text = data["choices"][0]["message"]["content"].strip()
        
        # ✅ Clean markdown code blocks
        response_text = response_text.replace('```json', '').replace('```', '').strip()

        # ✅ Try to extract JSON array
        match = re.search(r'\[[\s\S]*\]', response_text, re.S)
        if match:
            clean_json_text = match.group(0).strip()
        else:
            clean_json_text = response_text.strip()

        if not clean_json_text:
            raise RuntimeError("OpenRouter API mengembalikan respons kosong")

        # ✅ Try JSON parse with auto-fix, fallback to markdown parser
        exercises_data = None
        original_error = None
        
        try:
            exercises_data = json.loads(clean_json_text)
            logger.info(f"✅ Successfully parsed JSON: {len(exercises_data)} exercises")
            
        except json.JSONDecodeError as json_err:
            original_error = str(json_err)
            logger.warning(f"⚠️ JSON parse failed: {json_err}")
            
            # ✅ Try to fix incomplete JSON
            try:
                logger.info("🔧 Attempting to fix incomplete JSON...")
                fixed_json = clean_json_text
                
                # ✅ Fix 1: Add missing commas after string values
                # Pattern: "value"  \n  "nextKey" → "value",\n"nextKey"
                fixed_json = re.sub(r'"\s*\n\s*"', '",\n"', fixed_json)
                
                # ✅ Fix 2: Add missing commas after ] or }
                # Pattern: ]  \n  " → ],\n"
                fixed_json = re.sub(r'(\]|\})\s*\n\s*"', r'\1,\n"', fixed_json)
                
                # ✅ Fix 3: Close any open string
                if fixed_json.count('"') % 2 != 0:
                    fixed_json += '"'
                    logger.info("Added closing quote")
                
                # ✅ Fix 4: Count and add missing brackets
                open_braces = fixed_json.count('{')
                close_braces = fixed_json.count('}')
                open_brackets = fixed_json.count('[')
                close_brackets = fixed_json.count(']')
                
                # Add missing closing braces
                if open_braces > close_braces:
                    diff = open_braces - close_braces
                    fixed_json += '}' * diff
                    logger.info(f"Added {diff} closing braces")
                
                # Add missing closing brackets
                if open_brackets > close_brackets:
                    diff = open_brackets - close_brackets
                    fixed_json += ']' * diff
                    logger.info(f"Added {diff} closing brackets")
                
                logger.info("Fixed JSON preview:\n%s", fixed_json[:500])
                exercises_data = json.loads(fixed_json)
                logger.info(f"✅ Fixed and parsed JSON: {len(exercises_data)} exercises")
                
            except Exception as fix_error:
                logger.warning(f"⚠️ JSON fix failed: {fix_error}")
                
                # ✅ FALLBACK: Try markdown parser
                logger.info("🔄 Trying markdown parser...")
                try:
                    exercises_data = self.parse_markdown_exercises(response_text, request.num_questions)
                    if not exercises_data:
                        raise RuntimeError("Markdown parser returned no exercises")
                    logger.info(f"✅ Markdown parser succeeded: {len(exercises_data)} exercises")
                    
                except Exception as md_error:
                    logger.error(f"❌ All parsing methods failed")
                    logger.error(f"Response preview:\n{response_text[:1500]}")
                    raise RuntimeError(
                        f"Model mengembalikan data yang tidak bisa di-parse.\n"
                        f"Original JSON error: {original_error}\n"
                        f"Fix attempt: {fix_error}\n"
                        f"Markdown parser: {md_error}"
                    )

        # Validate exercises_data
        if not exercises_data or not isinstance(exercises_data, list):
            raise RuntimeError(f"Invalid exercises data format: {type(exercises_data)}")

        # 7️⃣ Konversi ke objek Exercise (with validation)
        exercises: List[Exercise] = []
        skipped = 0
        
        for idx, ex_data in enumerate(exercises_data):
            try:
                # Validate required fields
                if not ex_data.get("question"):
                    logger.warning(f"Exercise {idx}: Missing question, skipping")
                    skipped += 1
                    continue
                
                if not ex_data.get("options") or len(ex_data.get("options", [])) != 4:
                    logger.warning(f"Exercise {idx}: Invalid options (need 4), skipping")
                    skipped += 1
                    continue
                
                # Handle both "correct" and "correctAnswer"
                correct_val = ex_data.get("correct")
                if correct_val is None:
                    correct_val = ex_data.get("correctAnswer", 0)
                
                if not ex_data.get("explanation"):
                    logger.warning(f"Exercise {idx}: Missing explanation, skipping")
                    skipped += 1
                    continue
                
                # Create exercise
                # ✅ Get difficulty level (default to "medium" if not provided)
                difficulty = ex_data.get("difficulty", "medium").lower()
                if difficulty not in ["beginner", "medium", "advanced"]:
                    difficulty = "medium"

                exercise = Exercise(
                    id=str(uuid.uuid4()),
                    type=ex_data.get("type", "grammar"),
                    difficulty=difficulty,  # ✅ ADD difficulty field
                    question=ex_data["question"],
                    classic_text=ex_data.get("classicText"),
                    modern_text=ex_data.get("modernText"),
                    comic_reference=ex_data.get("comicReference"),
                    audio_text=ex_data.get("audioText"),
                    audio_type=ex_data.get("audioType"),
                    options=ex_data["options"],
                    correct=correct_val,
                    explanation=ex_data["explanation"],
                    grammar_rule=ex_data.get("grammarRule")
                )
                exercises.append(exercise)
                
            except Exception as e:
                logger.warning(f"Exercise {idx}: Failed to create - {e}, skipping")
                skipped += 1
                continue

        if skipped > 0:
            logger.warning(f"⚠️ Skipped {skipped} invalid exercises")

        if not exercises:
            raise RuntimeError("No valid exercises generated after parsing")

        logger.info(f"✅ Successfully created {len(exercises)} valid exercise objects")
        
        # ✅ RETURN WITH CHARACTERS
        return {
            'exercises': exercises,
            'characters': characters
        }

training_service = TrainingService()