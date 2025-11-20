# schemas.py
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import List, Optional

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str  # 'student' or 'teacher'
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes (bcrypt limit)')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username cannot be longer than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['student', 'teacher']:
            raise ValueError("Role must be 'student' or 'teacher'")
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Full name cannot be longer than 100 characters')
        return v.strip()

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str

class ClassicTextInput(BaseModel):
    text: str
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

class ModernTextResponse(BaseModel):
    original_text: str
    modern_text: str

class ComicPanel(BaseModel):
    id: int
    dialogue: str
    narration: str
    visual: str
    setting: str
    mood: str
    composition: str

class ComicScriptResponse(BaseModel):
    characters: Optional[List[dict]] = []
    panels: List[ComicPanel]
    raw_script: str

class ImageGenerationRequest(BaseModel):
    panel: ComicPanel
    width: int = 1024
    height: int = 1024
    steps: int = 25
    cfg: float = 7.5
    negative_prompt: str = "blurry, low quality, distorted, ugly, bad anatomy"
    seed: Optional[int] = None
    
    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v):
        if v < 256 or v > 2048:
            raise ValueError('Image dimensions must be between 256 and 2048 pixels')
        return v
    
    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Steps must be between 1 and 100')
        return v

class PanelImageResponse(BaseModel):
    panel_id: int
    image_url: str
    dialogue_audio_url: Optional[str] = None
    narration_audio_url: Optional[str] = None

class LearningModuleRequest(BaseModel):
    classic_text: str
    ai_model: Optional[str] = None
    temperature: float = 0.7
    image_width: int = 1024
    image_height: int = 1024
    generate_audio: bool = True
    
    @field_validator('classic_text')
    @classmethod
    def validate_classic_text(cls, v):
        if not v.strip():
            raise ValueError('Classic text cannot be empty')
        return v.strip()
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v

class LearningModuleResponse(BaseModel):
    module_id: str
    original_text: str
    modern_text: str
    panels: List[ComicPanel]
    panel_images: List[PanelImageResponse]
    status: str

# Training Schemas
class GrammarTopic(BaseModel):
    id: str
    label: str
    description: str
    is_basic: bool

class Exercise(BaseModel):
    id: str
    type: str
    question: str
    classic_text: Optional[str] = None
    modern_text: Optional[str] = None
    comic_reference: Optional[str] = None
    audio_text: Optional[str] = None
    audio_type: Optional[str] = None
    options: List[str]
    correct: int
    explanation: str
    grammar_rule: Optional[str] = None
    
    @field_validator('correct')
    @classmethod
    def validate_correct_answer(cls, v, info):
        # Validate that correct answer index is within options range
        if 'options' in info.data and v >= len(info.data['options']):
            raise ValueError('Correct answer index is out of range')
        return v

class TrainingRequest(BaseModel):
    classic_text: str
    modern_text: str
    panels: List[ComicPanel]
    selected_topics: List[str]
    num_questions: int = 5
    
    @field_validator('num_questions')
    @classmethod
    def validate_num_questions(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Number of questions must be between 1 and 50')
        return v

class TrainingResponse(BaseModel):
    exercises: List[Exercise]
    total_questions: int

class AnswerSubmission(BaseModel):
    exercise_id: str
    selected_answer: int
    
    @field_validator('selected_answer')
    @classmethod
    def validate_selected_answer(cls, v):
        if v < 0:
            raise ValueError('Selected answer must be non-negative')
        return v

class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: int
    explanation: str
    points_earned: int


# ============================================================================
# Exercise Editor Schemas (for CRUD operations on existing exercises)
# ============================================================================

class ExerciseEdit(BaseModel):
    """Schema for editing exercises (no id required, different field names)"""
    question: str
    type: str
    options: Optional[List[str]] = None  # Frontend sends list
    correct_answer: str  # ✅ Match database field name
    explanation: Optional[str] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = [
            'multiple_choice', 'fill_in_blank', 'true_false', 
            'matching', 'error_correction', 'transformation', 
            'ordering', 'completion', 'pronunciation', 'vocabulary'
        ]
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v

class ExerciseResponse(BaseModel):
    """Schema for returning exercise data"""
    id: int
    question: str
    type: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    attempts_count: int = 0
    can_delete: bool = True


# class ExerciseCreate(BaseModel):
#     """Schema for creating a new exercise (no id)"""
#     type: str
#     question: str
#     classic_text: Optional[str] = None
#     modern_text: Optional[str] = None
#     comic_reference: Optional[str] = None
#     audio_text: Optional[str] = None
#     audio_type: Optional[str] = None
#     options: List[str]
#     correct: int  # Pastikan frontend mengirim 'correct' sebagai integer (index)
#     explanation: str
#     grammar_rule: Optional[str] = None

#     # Anda bisa tambahkan validator dari 'Exercise' jika perlu
#     @field_validator('correct')
#     @classmethod
#     def validate_correct_answer(cls, v, info):
#         if 'options' in info.data and v >= len(info.data['options']):
#             raise ValueError('Correct answer index is out of range')
#         return v
