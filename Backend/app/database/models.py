# models.py - FIXED VERSION with Audio Support
from pony.orm import Database, Required, Optional, Set, Json, PrimaryKey
from datetime import datetime

db = Database()

class User(db.Entity):
    """User account with role-based access"""
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    email = Required(str, unique=True)
    hashed_password = Required(str)
    full_name = Required(str)
    role = Required(str)  # 'student' or 'teacher'
    is_active = Required(bool, default=True)
    created_at = Required(datetime, default=datetime.now)

    last_active = Optional(datetime, nullable=True)  # Last activity timestamp
    last_login = Optional(datetime, nullable=True)   # Last login timestamp
    login_count = Optional(int, default=0)           # Total number of logins
    
    progress_records = Set('UserProgress')

class LearningModule(db.Entity):
    """Main learning module containing comic and exercises"""
    id = PrimaryKey(str)
    module_name = Required(str) 
    classic_text = Required(str)
    modern_text = Required(str)
    comic_script = Required(str)
    created_at = Required(datetime, default=datetime.now)
    updated_at = Required(datetime, default=datetime.now)
    
    panels = Set('ComicPanel')
    exercises = Set('Exercise')
    user_progress = Set('UserProgress')

class ComicPanel(db.Entity):
    """Individual comic panel"""
    id = PrimaryKey(int, auto=True)
    module = Required(LearningModule)
    panel_number = Required(int)
    dialogue = Required(str)
    narration = Required(str)
    visual = Required(str)
    setting = Required(str)
    mood = Required(str)
    composition = Required(str)
    
    # ✅ FIXED: Image and Audio storage
    image_base64 = Optional(str, nullable=True)  # Panel image
    dialogue_audio_base64 = Optional(str, nullable=True)  # Dialogue audio
    narration_audio_base64 = Optional(str, nullable=True)  # Narration audio
    
    created_at = Required(datetime, default=datetime.now)

class Exercise(db.Entity):
    """Training exercise"""
    id = PrimaryKey(str)
    module = Required(LearningModule)
    type = Required(str)
    question = Required(str)
    classic_text = Optional(str, nullable=True)
    modern_text = Optional(str, nullable=True)
    comic_reference = Optional(str, nullable=True)
    audio_text = Optional(str, nullable=True)
    audio_type = Optional(str, nullable=True)
    options = Required(Json)
    correct_answer = Required(int)
    explanation = Required(str)
    grammar_rule = Optional(str, nullable=True)
    created_at = Required(datetime, default=datetime.now)
    
    user_answers = Set('UserAnswer')

class UserProgress(db.Entity):
    """Track user progress on modules"""
    id = PrimaryKey(int, auto=True)
    module = Required(LearningModule)
    user = Required(User)
    total_score = Required(int, default=0)
    correct_answers = Required(int, default=0)
    total_questions = Required(int, default=0)
    completed = Required(bool, default=False)
    started_at = Required(datetime, default=datetime.now)
    completed_at = Optional(datetime, nullable=True)
    
    answers = Set('UserAnswer')

class UserAnswer(db.Entity):
    """Individual answer to an exercise"""
    id = PrimaryKey(int, auto=True)
    progress = Required(UserProgress)
    exercise = Required(Exercise)
    selected_answer = Required(int)
    is_correct = Required(bool)
    answered_at = Required(datetime, default=datetime.now)