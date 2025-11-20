import logging
from pony.orm.core import Query
from fastapi import APIRouter, HTTPException, Depends, Query
from pony.orm import db_session, flush, commit
from datetime import datetime, timedelta
from typing import Annotated, List, Dict, Any
from pydantic import Field, constr
import uuid 
import logger
import base64


from app.database.models import (
    User, 
    LearningModule, 
    ComicPanel, 
    Exercise, 
    UserProgress, 
    UserAnswer
)
from app.routers.auth import get_current_user_from_token
from app.services.training_service import training_service
from app.services.tts_service import tts_service
from app.models.schemas import TrainingRequest

logger = logging.getLogger(__name__) 
router = APIRouter(prefix="/api/training", tags=["Training"])

# ✅ NEW: Helper function to convert audio bytes to base64
async def audio_blob_to_base64(audio_bytes: bytes) -> str:
    """Convert audio bytes to base64 string with data URI"""
    if not audio_bytes:
        return None
    
    b64_string = base64.b64encode(audio_bytes).decode('utf-8')
    return f"data:audio/mpeg;base64,{b64_string}"

# ✅ NEW ENDPOINT: Generate audio for panel
@router.post("/generate-panel-audio")
async def generate_panel_audio(
    data: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """Generate TTS audio for panel dialogue and narration"""
    try:
        dialogue = data.get('dialogue', '')
        narration = data.get('narration', '')
        
        result = {}
        
        # Generate dialogue audio
        if dialogue and dialogue.lower() != 'none':
            dialogue_audio_bytes = await tts_service.generate_audio(
                text=dialogue,
                voice_type='modern',
                use_ssml=False
            )
            if dialogue_audio_bytes:
                result['dialogue_audio'] = await audio_blob_to_base64(dialogue_audio_bytes)
                print(f"✅ Generated dialogue audio ({len(dialogue_audio_bytes)} bytes)")
        
        # Generate narration audio
        if narration:
            narration_audio_bytes = await tts_service.generate_audio(
                text=narration,
                voice_type='narrator',
                use_ssml=False
            )
            if narration_audio_bytes:
                result['narration_audio'] = await audio_blob_to_base64(narration_audio_bytes)
                print(f"✅ Generated narration audio ({len(narration_audio_bytes)} bytes)")
        
        return result
        
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to generate audio: {str(e)}")

@router.post("/create-module")
async def create_module(
    data: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """Teacher creates a new learning module"""
    try:
        # Check if user is teacher
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can create modules")
        
        user_id = current_user.id
        
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            module_id = f"module_{int(datetime.now().timestamp())}"
            
            # Create module
            module = LearningModule(
                id=module_id,
                classic_text=data.get('classic_text', ''),
                modern_text=data.get('modern_text', ''),
                comic_script=data.get('comic_script', ''),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save panels with images AND audio
            panels_data = data.get('panels', [])
            panel_images = data.get('panel_images', [])
            panel_audios = data.get('panel_audios', [])  # ✅ NEW
            
            for i, panel_data in enumerate(panels_data):
                # ✅ FIXED: Handle image with correct key priority
                image_base64 = None
                
                if i < len(panel_images):
                    img_data = panel_images[i]
                    if isinstance(img_data, dict):
                        # ✅ CRITICAL FIX: Check 'image_base64' FIRST!
                        image_base64 = (
                            img_data.get('image_base64') or  # ✅ Primary key
                            img_data.get('data') or 
                            img_data.get('image') or 
                            img_data.get('url') or
                            img_data.get('base64')
                        )
                    elif isinstance(img_data, str):
                        image_base64 = img_data
                
                # ✅ NEW: Handle audio data
                dialogue_audio = None
                narration_audio = None
                
                if i < len(panel_audios):
                    audio_data = panel_audios[i]
                    if isinstance(audio_data, dict):
                        dialogue_audio = audio_data.get('dialogue_audio')
                        narration_audio = audio_data.get('narration_audio')
                
                ComicPanel(
                    module=module,
                    panel_number=panel_data.get('id', i + 1),
                    dialogue=panel_data.get('dialogue', ''),
                    narration=panel_data.get('narration', ''),
                    visual=panel_data.get('visual', ''),
                    setting=panel_data.get('setting', ''),
                    mood=panel_data.get('mood', ''),
                    composition=panel_data.get('composition', ''),
                    image_base64=image_base64,
                    dialogue_audio_base64=dialogue_audio,  # ✅ NEW
                    narration_audio_base64=narration_audio,  # ✅ NEW
                    created_at=datetime.now()
                )
            
            flush()
            
            # Save exercises if provided
            exercises_data = data.get('exercises', [])
            
            for ex_data in exercises_data:
                Exercise(
                    id=ex_data.get('id', str(uuid.uuid4())),
                    module=module,
                    type=ex_data.get('type', 'multiple_choice'),
                    question=ex_data.get('question', ''),
                    classic_text=ex_data.get('classic_text'),
                    modern_text=ex_data.get('modern_text'),
                    comic_reference=ex_data.get('comic_reference'),
                    audio_text=ex_data.get('audio_text'),
                    audio_type=ex_data.get('audio_type'),
                    options=ex_data.get('options', []),
                    correct_answer=ex_data.get('correct', 0),
                    explanation=ex_data.get('explanation', ''),
                    grammar_rule=ex_data.get('grammar_rule'),
                    created_at=datetime.now()
                )
            
            commit()
            
            # ✅ NEW: Count images and audios
            images_saved = sum(1 for i in range(len(panels_data)) if i < len(panel_images) and panel_images[i])
            audios_saved = sum(1 for i in range(len(panels_data)) if i < len(panel_audios) and panel_audios[i])
            
            return {
                "success": True,
                "message": "Learning module created successfully",
                "module_id": module_id,
                "panels_saved": len(panels_data),
                "images_saved": images_saved,  # ✅ NEW
                "audios_saved": audios_saved,  # ✅ NEW
                "exercises_saved": len(exercises_data)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating module: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to create module: {str(e)}")

@router.get("/my-modules")
async def get_my_modules(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all modules created by current teacher"""
    try:
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can view their modules")
        
        with db_session:
            modules = LearningModule.select()[:]
            
            result = []
            for module in modules:
                # Count students who completed this module
                students_count = len(list(module.user_progress.select()))
                
                result.append({
                    "module_id": module.id,
                    "module_name": module.module_name,
                    "classic_text_preview": module.classic_text[:100] + "..." if len(module.classic_text) > 100 else module.classic_text,
                    "panels_count": len(list(module.panels)),
                    "exercises_count": len(list(module.exercises)),
                    "students_completed": students_count,
                    "created_at": module.created_at.isoformat(),
                    "updated_at": module.updated_at.isoformat()
                })
            
            return {
                "modules": result,
                "total_modules": len(result)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting modules: {e}")
        raise HTTPException(500, f"Failed to get modules: {str(e)}")

@router.get("/student-progress-overview")
async def get_student_progress_overview(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get overview of all students' progress"""
    try:
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can view student progress")
        
        with db_session:
            students = User.select(lambda u: u.role == 'student')[:]
            
            result = []
            for student in students:
                progress_records = list(student.progress_records.select())
                
                total_score = sum(p.total_score for p in progress_records)
                modules_completed = sum(1 for p in progress_records if p.completed)
                total_questions = sum(p.total_questions for p in progress_records)
                correct_answers = sum(p.correct_answers for p in progress_records)
                
                accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
                
                # Get latest activity
                latest_activity = max(
                    (p.completed_at for p in progress_records if p.completed_at),
                    default=None
                )
                
                result.append({
                    "student_id": student.id,
                    "username": student.username,
                    "full_name": student.full_name,
                    "email": student.email,
                    "total_score": total_score,
                    "modules_completed": modules_completed,
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "accuracy": round(accuracy, 1),
                    "latest_activity": latest_activity.isoformat() if latest_activity else None
                })
            
            # Sort by total score descending
            result.sort(key=lambda x: x['total_score'], reverse=True)
            
            return {
                "students": result,
                "total_students": len(result)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting student progress: {e}")
        raise HTTPException(500, f"Failed to get student progress: {str(e)}")

@router.get("/student-detail/{student_id}")
async def get_student_detail(
    student_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get detailed progress for a specific student"""
    try:
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can view student details")
        
        with db_session:
            student = User.get(id=student_id)
            if not student:
                raise HTTPException(404, "Student not found")
            
            if student.role != 'student':
                raise HTTPException(400, "User is not a student")
            
            progress_records = list(student.progress_records.select())
            
            modules_progress = []
            for prog in progress_records:
                # Get answers
                answers = list(prog.answers.select())
                
                modules_progress.append({
                    "module_id": prog.module.id,
                    "classic_text_preview": prog.module.classic_text[:100] + "...",
                    "total_score": prog.total_score,
                    "correct_answers": prog.correct_answers,
                    "total_questions": prog.total_questions,
                    "accuracy": round((prog.correct_answers / prog.total_questions * 100), 1) if prog.total_questions > 0 else 0,
                    "completed": prog.completed,
                    "started_at": prog.started_at.isoformat(),
                    "completed_at": prog.completed_at.isoformat() if prog.completed_at else None,
                    "answers_count": len(answers)
                })
            
            return {
                "student_id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "modules_progress": modules_progress,
                "total_modules": len(modules_progress),
                "total_score": sum(p['total_score'] for p in modules_progress)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting student detail: {e}")
        raise HTTPException(500, f"Failed to get student detail: {str(e)}")

@router.get("/topics")
async def get_topics():
    """Get available grammar topics for training"""
    return {"topics": training_service.GRAMMAR_TOPICS}

@router.post("/generate-exercises")
async def generate_exercises(
    request: TrainingRequest,
    current_user: User = Depends(get_current_user_from_token)
):
    """Generate training exercises using AI based on module content"""
    try:
        logger.info(f"📝 User {current_user.username} generating exercises")
        logger.info(f"   Topics: {request.selected_topics}")
        logger.info(f"   Questions: {request.num_questions}")
        
        # ✅ CHANGE: Result is now a dict with 'exercises' and 'characters'
        result = await training_service.generate_training_exercises(request)
        
        # ✅ CHANGE: Extract exercises and characters from dict
        exercises = result['exercises']
        characters = result.get('characters', [])
        
        logger.info(f"✅ Generated {len(exercises)} exercises")
        logger.info(f"✅ Extracted {len(characters)} characters for consistency")
        
        for char in characters:
            logger.info(f"   - [{char.get('id', '?')}] {char.get('name', 'Unknown')}")
        
        return {
            "exercises": [ex.dict() for ex in exercises],
            "characters": characters,  # ✅ ADD: Include characters
            "total_questions": len(exercises)
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating exercises: {e}", exc_info=True)
        print(f"Error generating exercises: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate exercises: {str(e)}"
        )

@router.post("/save-all-results")
async def save_all_results(
    data: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """Save complete training results including module, panels, exercises, and user progress"""
    try:
        user_id = current_user.id
        
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            module_id = f"module_{int(datetime.now().timestamp())}"
            
            # Create learning module
            module = LearningModule(
                id=module_id,
                classic_text=data.get('classic_text', ''),
                modern_text=data.get('modern_text', ''),
                comic_script=data.get('comic_script', ''),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # ✅ FIXED: Save comic panels with images AND audio
            panels_data = data.get('panels', [])
            panel_images = data.get('panel_images', [])
            panel_audios = data.get('panel_audios', [])  # ✅ NEW
            
            print(f"📦 Saving {len(panels_data)} panels")
            print(f"🖼️  Images: {len(panel_images)}")
            print(f"🔊 Audios: {len(panel_audios)}")
            
            images_count = 0
            audios_count = 0
            
            for i, panel_data in enumerate(panels_data):
                # ✅ FIXED: Handle image with correct key priority
                image_base64 = None
                
                if i < len(panel_images):
                    img_data = panel_images[i]
                    
                    if isinstance(img_data, dict):
                        # ✅ CRITICAL FIX: Check 'image_base64' key FIRST!
                        image_base64 = (
                            img_data.get('image_base64') or  # ✅ Primary key - matches frontend!
                            img_data.get('data') or 
                            img_data.get('image') or 
                            img_data.get('url') or 
                            img_data.get('base64')
                        )
                        if image_base64:
                            images_count += 1
                            print(f"Panel {i}: Image saved (from dict key: {[k for k in img_data.keys() if img_data[k] == image_base64][0]})")
                    
                    elif isinstance(img_data, str):
                        image_base64 = img_data
                        images_count += 1
                        print(f"Panel {i}: Image saved (from string, {len(img_data)} chars)")
                    
                    else:
                        print(f"Panel {i}: No image (type: {type(img_data)})")
                
                # ✅ NEW: Handle audio data
                dialogue_audio = None
                narration_audio = None
                
                if i < len(panel_audios):
                    audio_data = panel_audios[i]
                    if isinstance(audio_data, dict):
                        dialogue_audio = audio_data.get('dialogue_audio')
                        narration_audio = audio_data.get('narration_audio')
                        
                        if dialogue_audio or narration_audio:
                            audios_count += (1 if dialogue_audio else 0) + (1 if narration_audio else 0)
                            print(f"Panel {i}: Audio saved - dialogue: {bool(dialogue_audio)}, narration: {bool(narration_audio)}")
                
                # ✅ Save panel with all data
                ComicPanel(
                    module=module,
                    panel_number=panel_data.get('id', i + 1),
                    dialogue=panel_data.get('dialogue', ''),
                    narration=panel_data.get('narration', ''),
                    visual=panel_data.get('visual', ''),
                    setting=panel_data.get('setting', ''),
                    mood=panel_data.get('mood', ''),
                    composition=panel_data.get('composition', ''),
                    image_base64=image_base64,
                    dialogue_audio_base64=dialogue_audio,  # ✅ NEW
                    narration_audio_base64=narration_audio,  # ✅ NEW
                    created_at=datetime.now()
                )
            
            flush()
            print(f"✅ Saved {len(panels_data)} panels ({images_count} images, {audios_count} audios)")
            
            # Save exercises
            exercises_data = data.get('exercises', [])
            saved_exercises = {}
            
            print(f"Saving {len(exercises_data)} exercises")
            
            for ex_data in exercises_data:
                exercise = Exercise(
                    id=ex_data.get('id', str(uuid.uuid4())),
                    module=module,
                    type=ex_data.get('type', 'multiple_choice'),
                    question=ex_data.get('question', ''),
                    classic_text=ex_data.get('classic_text'),
                    modern_text=ex_data.get('modern_text'),
                    comic_reference=ex_data.get('comic_reference'),
                    audio_text=ex_data.get('audio_text'),
                    audio_type=ex_data.get('audio_type'),
                    options=ex_data.get('options', []),
                    correct_answer=ex_data.get('correct', 0),
                    explanation=ex_data.get('explanation', ''),
                    grammar_rule=ex_data.get('grammar_rule'),
                    created_at=datetime.now()
                )
                saved_exercises[ex_data.get('id')] = exercise
            
            flush()
            print(f"✅ Saved {len(exercises_data)} exercises")
            
            # Calculate user stats
            user_answers_data = data.get('user_answers', [])
            correct_count = sum(1 for ans in user_answers_data if ans.get('is_correct', False))
            total_questions = len(user_answers_data)
            score = data.get('score', 0)
            
            print(f"User stats: {correct_count}/{total_questions} correct, score: {score}")
            
            # Create user progress
            progress = UserProgress(
                module=module,
                user=user,
                total_score=score,
                correct_answers=correct_count,
                total_questions=total_questions,
                completed=True,
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            flush()
            print(f"✅ Saved user progress")
            
            # Save individual user answers
            print(f"Saving {len(user_answers_data)} user answers")
            
            for answer_data in user_answers_data:
                exercise_id = answer_data.get('exercise_id', '')
                exercise = saved_exercises.get(exercise_id)
                
                if exercise:
                    UserAnswer(
                        progress=progress,
                        exercise=exercise,
                        selected_answer=answer_data.get('selected_answer', 0),
                        is_correct=answer_data.get('is_correct', False),
                        answered_at=datetime.now()
                    )
                else:
                    print(f"⚠️  Warning: Exercise {exercise_id} not found for answer")
            
            commit()
            print(f"✅ All data committed to database")
            
            return {
                "success": True,
                "message": "Training results saved successfully",
                "module_id": module_id,
                "score": score,
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "panels_saved": len(panels_data),
                "images_saved": images_count,  # ✅ NEW
                "audios_saved": audios_count,  # ✅ NEW
                "exercises_saved": len(exercises_data),
                "answers_saved": len(user_answers_data)
            }
            
    except Exception as e:
        print(f"❌ Failed to save all results: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save results: {str(e)}"
        )

@router.get("/progress")
async def get_my_progress(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get current user's training progress"""
    try:
        user_id = current_user.id
        
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            progress_records = list(user.progress_records.select())
            
            result = []
            for prog in progress_records:
                result.append({
                    "module_id": prog.module.id,
                    "classic_text_preview": prog.module.classic_text[:100] + "..." if len(prog.module.classic_text) > 100 else prog.module.classic_text,
                    "total_score": prog.total_score,
                    "correct_answers": prog.correct_answers,
                    "total_questions": prog.total_questions,
                    "completed": prog.completed,
                    "started_at": prog.started_at.isoformat(),
                    "completed_at": prog.completed_at.isoformat() if prog.completed_at else None
                })
            
            return {
                "user_id": user_id,
                "username": user.username,
                "progress": result,
                "total_modules": len(result),
                "total_score": sum(p["total_score"] for p in result)
            }
            
    except Exception as e:
        print(f"Error getting progress: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get progress: {str(e)}"
        )
    
@router.get("/leaderboard")
async def get_leaderboard(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    time_period: Annotated[str, Query(pattern="^(all_time|this_month|this_week)$")] = "all_time",
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get leaderboard rankings
    
    Parameters:
    - limit: Number of top students to return (default 10)
    - time_period: all_time, this_month, this_week
    """
    try:
        with db_session:
            # Get all students
            all_students = list(User.select(lambda u: u.role == 'student'))
            
            # Calculate time filter
            now = datetime.now()
            if time_period == "this_week":
                start_date = now - timedelta(days=now.weekday())
            elif time_period == "this_month":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = None
            
            leaderboard_data = []
            
            for student in all_students:
                progress_list = list(student.progress_records)
                
                # Filter by time period
                if start_date:
                    progress_list = [p for p in progress_list if p.started_at >= start_date]
                
                if not progress_list:
                    continue
                
                total_score = sum(p.total_score for p in progress_list)
                modules_completed = sum(1 for p in progress_list if p.completed)
                total_questions = sum(p.total_questions for p in progress_list)
                correct_answers = sum(p.correct_answers for p in progress_list)
                
                accuracy = 0
                if total_questions > 0:
                    accuracy = round((correct_answers / total_questions) * 100, 2)
                
                # Determine badges
                badges = []
                if modules_completed >= 10:
                    badges.append('🏆 Master Learner')
                elif modules_completed >= 5:
                    badges.append('📚 Dedicated Student')
                elif modules_completed >= 1:
                    badges.append('🌟 First Steps')
                
                if accuracy >= 90:
                    badges.append('🎯 Perfect Accuracy')
                elif accuracy >= 80:
                    badges.append('✨ High Achiever')
                
                if total_score >= 1000:
                    badges.append('💎 Score Champion')
                elif total_score >= 500:
                    badges.append('⭐ Rising Star')
                
                leaderboard_data.append({
                    'student_id': student.id,
                    'student_name': student.full_name,
                    'username': student.username,
                    'total_score': total_score,
                    'modules_completed': modules_completed,
                    'accuracy': accuracy,
                    'badges': badges,
                    'is_current_user': student.id == current_user.id
                })
            
            # Sort by total score
            leaderboard_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Add ranks
            for idx, student in enumerate(leaderboard_data, 1):
                student['rank'] = idx
            
            # Limit results
            top_students = leaderboard_data[:limit]
            
            # Find current user's position
            current_user_rank = None
            if current_user.role == 'student':
                for student in leaderboard_data:
                    if student['student_id'] == current_user.id:
                        current_user_rank = student
                        break
            
            return {
                'leaderboard': top_students,
                'total_students': len(leaderboard_data),
                'current_user_rank': current_user_rank,
                'time_period': time_period
            }
    
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get leaderboard: {str(e)}")
    

@router.post("/save-module-exercises")
async def save_module_with_exercises(
    request: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Save module + exercises (TEACHER ONLY - no student answers)
    """
    try:
        # ✅ Only teachers can create modules
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can create modules")
        
        logger.info(f"👨‍🏫 Teacher {current_user.username} saving module + exercises")
        
        with db_session:
            # ✅ Generate unique module ID
            module_id = f"module_{int(datetime.now().timestamp())}"
            
            # ✅ Get module name safely from request
            module_name = request.get('module_name', '').strip()
            if not module_name:
                module_name = f"Module {module_id}"  # fallback if not provided
            
            logger.info(f"📝 Module name received: {module_name}")
            
            # 1. Create module
            module = LearningModule(
                id=module_id,
                module_name=module_name,  # ✅ ADD THIS LINE
                classic_text=request['classic_text'],
                modern_text=request['modern_text'],
                comic_script=request['comic_script'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            flush()
            
            logger.info(f"✅ Module created: {module.id}")
            
            # 2. Save panels with images and audio
            panels_data = request.get('panels', [])
            panel_images = request.get('panel_images', [])
            panel_audios = request.get('panel_audios', [])
            
            # Create mapping for quick lookup
            image_map = {img['panel_id']: img['image_base64'] for img in panel_images if 'panel_id' in img and 'image_base64' in img}
            audio_map = {}
            for audio in panel_audios:
                panel_id = audio.get('panel_id')
                if panel_id:
                    if panel_id not in audio_map:
                        audio_map[panel_id] = {}
                    audio_type = audio.get('type', 'dialogue')
                    audio_map[panel_id][audio_type] = audio.get('audio_base64')
            
            panels_saved = 0
            for panel_data in panels_data:
                panel_id = panel_data.get('id')
                
                ComicPanel(
                    module=module,
                    panel_number=panel_data.get('panel_number', panels_saved + 1),
                    dialogue=panel_data.get('dialogue', ''),
                    narration=panel_data.get('narration', ''),
                    visual=panel_data.get('visual', ''),
                    setting=panel_data.get('setting', ''),
                    mood=panel_data.get('mood', ''),
                    composition=panel_data.get('composition', ''),
                    image_base64=image_map.get(panel_id),
                    dialogue_audio_base64=audio_map.get(panel_id, {}).get('dialogue'),
                    narration_audio_base64=audio_map.get(panel_id, {}).get('narration'),
                    created_at=datetime.now()
                )
                panels_saved += 1
            
            flush()
            logger.info(f"✅ Saved {panels_saved} panels")
            
            # 3. Save exercises (NO answers yet - students will add later)
            exercises_data = request.get('exercises', [])
            exercises_saved = 0
            
            for ex_data in exercises_data:
                Exercise(
                    id=ex_data.get('id', str(uuid.uuid4())),
                    module=module,
                    type=ex_data.get('type', 'grammar'),
                    question=ex_data['question'],
                    classic_text=ex_data.get('classic_text'),
                    modern_text=ex_data.get('modern_text'),
                    comic_reference=ex_data.get('comic_reference'),
                    audio_text=ex_data.get('audio_text'),
                    audio_type=ex_data.get('audio_type'),
                    options=ex_data['options'],
                    correct_answer=ex_data['correct'],
                    explanation=ex_data['explanation'],
                    grammar_rule=ex_data.get('grammar_rule'),
                    created_at=datetime.now()
                )
                exercises_saved += 1
            
            commit()
            logger.info(f"✅ Saved {exercises_saved} exercises")
            
            return {
                'success': True,
                'module_id': module.id,
                'module_name': module.module_name,  # ✅ optionally include in response
                'panels_saved': panels_saved,
                'images_saved': len(panel_images),
                'audios_saved': len(panel_audios),
                'exercises_saved': exercises_saved,
                'message': 'Module and exercises saved successfully. Students can now start training.'
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving module: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to save module: {str(e)}")
    


@router.get("/my-modules")
async def get_my_modules(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all modules created by current teacher"""
    try:
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can view their modules")
        
        with db_session:
            modules = LearningModule.select()[:]
            
            result = []
            for module in modules:
                # Count students who completed this module
                students_count = len(list(module.user_progress.select()))
                
                # ✅ FIX: Get actual counts
                panels_count = len(list(module.panels))
                exercises_count = len(list(module.exercises))
                
                result.append({
                    "id": module.id,  # ✅ Changed from module_id
                    "module_name": module.module_name or "Untitled Module",  # ✅ Add fallback
                    "classic_text": module.classic_text,  # ✅ Full text, not preview
                    "panels_count": panels_count,  # ✅ Actual count
                    "panel_count": panels_count,  # ✅ Alias for frontend
                    "exercises_count": exercises_count,  # ✅ Actual count
                    "exercise_count": exercises_count,  # ✅ Alias for frontend
                    "students_completed": students_count,
                    "created_at": module.created_at.isoformat(),
                    "updated_at": module.updated_at.isoformat()
                })
            
            return {
                "modules": result,
                "total_modules": len(result)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting modules: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get modules: {str(e)}")


@router.get("/modules/{module_id}")
async def get_module_detail(
    module_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get module detail with panels and exercises"""
    try:
        with db_session:
            module = LearningModule.get(id=module_id)
            if not module:
                raise HTTPException(404, "Module not found")
            
            # Get panels
            panels = []
            for panel in sorted(module.panels, key=lambda p: p.panel_number):
                panels.append({
                    'id': panel.panel_number,
                    'panel_number': panel.panel_number,
                    'dialogue': panel.dialogue,
                    'narration': panel.narration,
                    'visual': panel.visual,
                    'setting': panel.setting,
                    'mood': panel.mood,
                    'composition': panel.composition,
                    'image_base64': panel.image_base64,
                    'dialogue_audio_base64': panel.dialogue_audio_base64,
                    'narration_audio_base64': panel.narration_audio_base64
                })
            
            # Get exercises
            exercises = []
            for exercise in module.exercises:
                exercises.append({
                    'id': exercise.id,
                    'type': exercise.type,
                    'question': exercise.question,
                    'classic_text': exercise.classic_text,
                    'modern_text': exercise.modern_text,
                    'comic_reference': exercise.comic_reference,
                    'audio_text': exercise.audio_text,
                    'audio_type': exercise.audio_type,
                    'options': exercise.options,
                    'correct': exercise.correct_answer,
                    'explanation': exercise.explanation,
                    'grammar_rule': exercise.grammar_rule
                })
            
            return {
                'id': module.id,
                'classic_text': module.classic_text,
                'modern_text': module.modern_text,
                'comic_script': module.comic_script,
                'panels': panels,
                'exercises': exercises
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module detail: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get module detail: {str(e)}")
    

@router.post("/save-student-answers")
async def save_student_answers(
    data: dict,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Save student answers and progress (module already exists)
    """
    try:
        if current_user.role != 'student':
            raise HTTPException(403, "Only students can save answers")
        
        module_id = data.get('module_id')
        if not module_id:
            raise HTTPException(400, "module_id is required")
        
        with db_session:
            # Check if module exists
            module = LearningModule.get(id=module_id)
            if not module:
                raise HTTPException(404, f"Module {module_id} not found")
            
            user = User.get(id=current_user.id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Get user answers data
            user_answers_data = data.get('user_answers', [])
            score = data.get('score', 0)
            
            # Count correct answers
            correct_count = sum(1 for ans in user_answers_data if ans.get('is_correct', False))
            total_questions = len(user_answers_data)
            
            logger.info(f"Student {user.username} saving answers: {correct_count}/{total_questions} correct, score: {score}")
            
            # Create or update user progress
            progress = UserProgress.get(module=module, user=user)
            
            if progress:
                # Update existing progress
                progress.total_score = score
                progress.correct_answers = correct_count
                progress.total_questions = total_questions
                progress.completed = True
                progress.completed_at = datetime.now()
                logger.info(f"Updated existing progress for student {user.username}")
            else:
                # Create new progress
                progress = UserProgress(
                    module=module,
                    user=user,
                    total_score=score,
                    correct_answers=correct_count,
                    total_questions=total_questions,
                    completed=True,
                    started_at=datetime.now(),
                    completed_at=datetime.now()
                )
                logger.info(f"Created new progress for student {user.username}")
            
            flush()
            
            # ✅ FIXED: Delete old answers if retrying
            progress_id = progress.id  # Get ID outside lambda
            old_answers = UserAnswer.select(lambda a: a.progress.id == progress_id)
            for old_answer in old_answers:
                old_answer.delete()
            
            flush()  # ✅ Commit deletion
            
            # Save new answers
            answers_saved = 0
            for answer_data in user_answers_data:
                exercise_id = answer_data.get('exercise_id', '')
                exercise = Exercise.get(id=exercise_id)
                
                if exercise:
                    UserAnswer(
                        progress=progress,
                        exercise=exercise,
                        selected_answer=answer_data.get('selected_answer', 0),
                        is_correct=answer_data.get('is_correct', False),
                        answered_at=datetime.now()
                    )
                    answers_saved += 1
                else:
                    logger.warning(f"Exercise {exercise_id} not found for answer")
            
            commit()
            logger.info(f"✅ Saved {answers_saved} answers for student {user.username}")
            
            return {
                "success": True,
                "message": "Student answers saved successfully",
                "module_id": module_id,
                "score": score,
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "answers_saved": answers_saved
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving student answers: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to save student answers: {str(e)}")