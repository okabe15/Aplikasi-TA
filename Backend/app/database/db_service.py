from pony.orm import Database, db_session, select, desc, commit
from app.database.models import db, LearningModule, ComicPanel, Exercise, UserProgress, UserAnswer, User
from app.models.schemas import ComicPanel as ComicPanelSchema, Exercise as ExerciseSchema
from typing import List, Optional
import uuid
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/elearning.sqlite')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

db.bind(provider='sqlite', filename=DB_PATH, create_db=True)
db.generate_mapping(create_tables=True)

class DatabaseService:
    
    @db_session
    def create_module(self, classic_text: str, modern_text: str, comic_script: str) -> str:
        """Create a new learning module"""
        module_id = str(uuid.uuid4())
        
        module = LearningModule(
            id=module_id,
            classic_text=classic_text,
            modern_text=modern_text,
            comic_script=comic_script
        )
        
        return module_id
    
    @db_session
    def save_panel(self, module_id: str, panel_data: ComicPanelSchema, image_path: Optional[str] = None):
        """Save a comic panel to database"""
        module = LearningModule[module_id]
        
        panel = ComicPanel(
            module=module,
            panel_number=panel_data.id,
            dialogue=panel_data.dialogue,
            narration=panel_data.narration,
            visual=panel_data.visual,
            setting=panel_data.setting,
            mood=panel_data.mood,
            composition=panel_data.composition,
            image_path=image_path if image_path else ""
        )
        
        return panel.id
    
    @db_session
    def save_panels(self, module_id: str, panels: List[ComicPanelSchema]):
        """Save multiple comic panels"""
        for panel in panels:
            self.save_panel(module_id, panel)
    
    @db_session
    def save_exercise(self, module_id: str, exercise_data: ExerciseSchema):
        """Save a training exercise"""
        module = LearningModule[module_id]
        
        exercise = Exercise(
            id=exercise_data.id,
            module=module,
            type=exercise_data.type,
            question=exercise_data.question,
            classic_text=exercise_data.classic_text if exercise_data.classic_text else "",
            modern_text=exercise_data.modern_text if exercise_data.modern_text else "",
            comic_reference=exercise_data.comic_reference if exercise_data.comic_reference else "",
            audio_text=exercise_data.audio_text if exercise_data.audio_text else "",
            audio_type=exercise_data.audio_type if exercise_data.audio_type else "",
            options=exercise_data.options,
            correct_answer=exercise_data.correct,
            explanation=exercise_data.explanation,
            grammar_rule=exercise_data.grammar_rule if exercise_data.grammar_rule else ""
        )
        
        return exercise.id
    
    @db_session
    def save_exercises(self, module_id: str, exercises: List[ExerciseSchema]):
        """Save multiple exercises"""
        for exercise in exercises:
            self.save_exercise(module_id, exercise)
    
    @db_session
    def list_modules(self, limit: int = 50):
        """List all learning modules with their stats"""
        try:
            modules = LearningModule.select().order_by(
                lambda m: desc(m.created_at)
            ).limit(limit)[:]
            
            result = []
            for module in modules:
                panel_count = module.panels.count()
                exercise_count = module.exercises.count()
                
                result.append({
                    "id": module.id,
                    "module_name": module.module_name or f"Module {module.id.replace('module_', '')}",  # ✅ ADD THIS
                    "classic_text": module.classic_text[:200] if module.classic_text else "",
                    "modern_text": module.modern_text[:200] if module.modern_text else "",
                    "panel_count": panel_count,
                    "exercise_count": exercise_count,
                    "created_at": module.created_at.isoformat(),
                    "updated_at": module.updated_at.isoformat()
                })
            
            return result
                
        except Exception as e:
            logger.error(f"Error listing modules: {e}")
            raise Exception(f"Failed to list modules: {str(e)}")

    @db_session
    def get_module(self, module_id: str) -> Optional[dict]:
        """Get module with all its data including base64 images"""
        try:
            module = LearningModule.get(id=module_id)
            if not module:
                return None
            
            # Get panels
            panels = []
            for p in module.panels.select().order_by(ComicPanel.panel_number):
                panels.append({
                    'id': p.panel_number,
                    'panel_number': p.panel_number,
                    'dialogue': p.dialogue or "",
                    'narration': p.narration or "",
                    'visual': p.visual or "",
                    'setting': p.setting or "",
                    'mood': p.mood or "",
                    'composition': p.composition or "",
                    'image_base64': p.image_base64 if p.image_base64 else None,
                    'created_at': p.created_at.isoformat() if p.created_at else ""
                })
            
            # Get exercises
            exercises = []
            for e in module.exercises.select():
                exercises.append({
                    'id': e.id,
                    'type': e.type or "multiple_choice",
                    'question': e.question or "",
                    'classic_text': e.classic_text if e.classic_text else None,
                    'modern_text': e.modern_text if e.modern_text else None,
                    'comic_reference': e.comic_reference if e.comic_reference else None,
                    'audio_text': e.audio_text if e.audio_text else None,
                    'audio_type': e.audio_type if e.audio_type else None,
                    'options': e.options or [],
                    'correct': e.correct_answer or 0,
                    'explanation': e.explanation or "",
                    'grammar_rule': e.grammar_rule if e.grammar_rule else None,
                    'created_at': e.created_at.isoformat() if e.created_at else ""
                })
            
            return {
                'id': module.id,
                'classic_text': module.classic_text or "",
                'modern_text': module.modern_text or "",
                'comic_script': module.comic_script or "",
                'panels': panels,
                'exercises': exercises,
                'created_at': module.created_at.isoformat(),
                'updated_at': module.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting module {module_id}: {e}")
            raise Exception(f"Failed to get module: {str(e)}")

    @db_session
    def delete_module(self, module_id: str) -> bool:
        """Delete a module and all related data"""
        try:
            module = LearningModule.get(id=module_id)
            if not module:
                return False
            
            # Delete related data first
            for panel in module.panels:
                panel.delete()
            
            for exercise in module.exercises:
                exercise.delete()
            
            for progress in module.user_progress:
                # Delete user answers for this progress
                for answer in progress.answers:
                    answer.delete()
                progress.delete()
            
            # Finally delete the module
            module.delete()
            commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting module {module_id}: {e}")
            raise Exception(f"Failed to delete module: {str(e)}")
    
    @db_session
    def create_user_progress(self, module_id: str, user_id: str = "default") -> int:
        """Create a new user progress entry"""
        module = LearningModule[module_id]
        
        progress = UserProgress(
            module=module,
            user_id=user_id
        )
        
        return progress.id
    
    @db_session
    def save_user_answer(self, progress_id: int, exercise_id: str, selected_answer: int, is_correct: bool):
        """Save a user's answer to an exercise"""
        progress = UserProgress[progress_id]
        exercise = Exercise[exercise_id]
        
        answer = UserAnswer(
            progress=progress,
            exercise=exercise,
            selected_answer=selected_answer,
            is_correct=is_correct
        )
        
        progress.total_questions += 1
        if is_correct:
            progress.correct_answers += 1
            progress.total_score += 10
        
        return answer.id
    
    @db_session
    def complete_module(self, progress_id: int):
        """Mark module as completed"""
        progress = UserProgress[progress_id]
        progress.completed = True
        progress.completed_at = datetime.now()
    
    @db_session
    def get_user_progress(self, module_id: str, user_id: str = "default") -> Optional[dict]:
        """Get user progress for a module"""
        progress = UserProgress.get(module_id=module_id, user_id=user_id)
        if not progress:
            return None
        
        return {
            'id': progress.id,
            'total_score': progress.total_score,
            'correct_answers': progress.correct_answers,
            'total_questions': progress.total_questions,
            'completed': progress.completed,
            'started_at': progress.started_at.isoformat(),
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
        }
    
def save_panel_audio(self, module_id: str, panel_id: int, dialogue_audio: str = None, narration_audio: str = None):
    """
    Save audio files for a panel
    
    Args:
        module_id: Module ID
        panel_id: Panel ID
        dialogue_audio: Base64 encoded dialogue audio
        narration_audio: Base64 encoded narration audio
    """
    try:
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        if dialogue_audio:
            update_data["dialogue_audio"] = dialogue_audio
        
        if narration_audio:
            update_data["narration_audio"] = narration_audio
        
        # Update atau insert audio data
        self.db.panels.update_one(
            {"module_id": module_id, "id": panel_id},
            {"$set": update_data},
            upsert=True
        )
        
        logger.info(f"✅ Saved audio for panel {panel_id} in module {module_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save panel audio: {str(e)}")
        raise


def get_panel_audio(self, module_id: str, panel_id: int, audio_type: str):
    """
    Get audio file for a panel
    
    Args:
        module_id: Module ID
        panel_id: Panel ID
        audio_type: 'dialogue' or 'narration'
    
    Returns:
        Base64 encoded audio data or None
    """
    try:
        panel = self.db.panels.find_one(
            {"module_id": module_id, "id": panel_id}
        )
        
        if not panel:
            logger.warning(f"Panel {panel_id} not found in module {module_id}")
            return None
        
        if audio_type == "dialogue":
            audio = panel.get("dialogue_audio")
        elif audio_type == "narration":
            audio = panel.get("narration_audio")
        else:
            logger.warning(f"Invalid audio_type: {audio_type}")
            return None
        
        if audio:
            logger.info(f"✅ Found {audio_type} audio for panel {panel_id}")
        else:
            logger.info(f"⚠️ No {audio_type} audio for panel {panel_id}")
        
        return audio
        
    except Exception as e:
        logger.error(f"❌ Failed to get panel audio: {str(e)}")
        raise


def get_module_with_audio(self, module_id: str):
    """
    Get module with all panels including audio data
    
    Args:
        module_id: Module ID
    
    Returns:
        Module dict with panels including audio
    """
    try:
        module = self.get_module(module_id)
        
        if not module:
            return None
        
        # Get panels with audio
        panels = list(self.db.panels.find(
            {"module_id": module_id},
            {"_id": 0}  # Exclude MongoDB _id
        ))
        
        module["panels"] = panels
        
        # Count panels with audio
        dialogue_count = sum(1 for p in panels if p.get("dialogue_audio"))
        narration_count = sum(1 for p in panels if p.get("narration_audio"))
        
        module["audio_stats"] = {
            "total_panels": len(panels),
            "dialogue_audio_count": dialogue_count,
            "narration_audio_count": narration_count
        }
        
        logger.info(f"✅ Retrieved module {module_id} with {len(panels)} panels")
        logger.info(f"   Audio: {dialogue_count} dialogues, {narration_count} narrations")
        
        return module
        
    except Exception as e:
        logger.error(f"❌ Failed to get module with audio: {str(e)}")
        raise


db_service = DatabaseService()