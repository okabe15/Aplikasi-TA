from pony.orm import commit, count, db_session, select
# from sqlalchemy import desc
from app.routers.auth import get_current_user_from_token
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from app.models.schemas import *
from app.models.schemas import ExerciseEdit, ExerciseResponse
from app.services.ai_service import ai_service
from app.services.comfyui_service import comfyui_service
from app.services.tts_service import tts_service
from app.services.auth_service import auth_service
from app.database.db_service import db_service
from app.database.models import LearningModule, User, UserAnswer
import io
import logging
import base64
import json
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/modules", tags=["Learning Modules"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Dependency to get current teacher user
async def get_current_teacher(token: str = Depends(oauth2_scheme)):
    """Verify user is a teacher"""
    return auth_service.get_current_active_teacher(token)

# PUBLIC ENDPOINTS (all users can access)

@router.get("")
async def list_modules(limit: int = 50):
    """List all learning modules"""
    try:
        with db_session:
            # ✅ Simplest query - get all, sort in Python
            all_modules = list(LearningModule.select())
            
            # Sort by created_at descending
            all_modules.sort(key=lambda m: m.created_at, reverse=True)
            
            # Take first N
            modules = all_modules[:limit]
            
            result = []
            for module in modules:
                panels_count = module.panels.count()
                exercises_count = module.exercises.count()
                
                result.append({
                    "id": module.id,
                    "module_name": module.module_name or f"Module {module.id.replace('module_', '')}",
                    "classic_text": module.classic_text[:200] if module.classic_text else "",
                    "panel_count": panels_count,
                    "exercise_count": exercises_count,
                    "created_at": module.created_at.isoformat()
                })
            
            return {"modules": result, "count": len(result)}
            
    except Exception as e:
        logger.error(f"Error listing modules: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list modules: {str(e)}")


# ✅ FIXED: Generate Audio Endpoint with better error handling
@router.get("/generate-audio")
async def generate_audio(
    text: str = Query(..., description="Text to synthesize"),
    voice_type: str = Query("modern", description="Voice type: modern, classic, narrator, male, female"),
    rate: str = Query("medium", description="Speech rate: slow, medium, fast"),
    pitch: str = Query("medium", description="Voice pitch: low, medium, high"),
    use_ssml: bool = Query(False, description="Use SSML formatting")
):
    """
    🎵 Generate TTS audio from text - PUBLIC ENDPOINT
    
    This endpoint is public so students and teachers can generate audio without authentication.
    Text is automatically cleaned to remove markdown and XML artifacts.
    
    Args:
        text: Text to synthesize (will be cleaned automatically)
        voice_type: Voice type (modern, classic, narrator, male, female)
        rate: Speech rate (slow, medium, fast)
        pitch: Voice pitch (low, medium, high)
        use_ssml: Use SSML formatting (not recommended for clean audio)
    
    Returns:
        Audio file as MP3 stream
    """
    try:
        logger.info(f"🎵 Audio generation request:")
        logger.info(f"  Text: {text[:50]}...")
        logger.info(f"  Voice: {voice_type}")
        logger.info(f"  Rate: {rate}, Pitch: {pitch}, SSML: {use_ssml}")
        
        # Validate text
        if not text or text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        # Generate audio using TTS service
        # TTS service automatically cleans the text!
        audio_data = await tts_service.generate_audio(
            text=text,
            voice_type=voice_type,
            rate=rate,
            pitch=pitch,
            use_ssml=use_ssml
        )
        
        if not audio_data:
            logger.error("❌ TTS service returned no audio data")
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        logger.info(f"✅ Audio generated successfully: {len(audio_data)} bytes")
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Audio generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

@router.get("/voices")
async def list_voices():
    """
    List available TTS voices - PUBLIC ENDPOINT
    
    Returns:
        Dictionary with available voices and their descriptions
    """
    try:
        voices = tts_service.get_available_voices()
        return voices
    except Exception as e:
        logger.error(f"❌ Error listing voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list voices")
    
@router.get("/{module_id}")
async def get_module(module_id: str):
    """Get a specific module with all its data (PUBLIC - all users can view)"""
    try:
        module = db_service.get_module(module_id)
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        return module
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get module: {str(e)}")


# TEACHER-ONLY ENDPOINTS (protected)

@router.post("/modernize-text", response_model=ModernTextResponse)
async def modernize_text(
    input_data: ClassicTextInput,
    current_teacher: User = Depends(get_current_teacher)
):
    """Step 1: Convert classic English to modern English (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} modernizing text")
        modern_text = await ai_service.modernize_text(input_data.text)
        
        return ModernTextResponse(
            original_text=input_data.text,
            modern_text=modern_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modernize text: {str(e)}")

@router.post("/generate-comic-script", response_model=ComicScriptResponse)
async def generate_comic_script(
    modernized: ModernTextResponse,
    current_teacher: User = Depends(get_current_teacher)
):
    """Step 2: Generate comic script from modern text (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} generating comic script")
        
        # ✅ UPDATED: Pass both classic and modern text
        result = await ai_service.generate_comic_script(
            classic_text=modernized.original_text,
            modern_text=modernized.modern_text
        )
        
        # ✅ UPDATED: Extract script and characters
        script_text = result['script']
        characters = result.get('characters', [])
        
        logger.info(f"✅ Generated script with {len(characters)} characters")
        
        # Parse script into panels
        panels = ai_service.parse_comic_script(script_text)
        
        logger.info(f"✅ Parsed {len(panels)} panels")
        
        # ✅ Try to return with characters, fallback if schema doesn't support it
        try:
            return ComicScriptResponse(
                panels=panels,
                raw_script=script_text,
                characters=characters
            )
        except Exception as schema_error:
            # If ComicScriptResponse doesn't have characters field yet
            logger.warning(f"⚠️ Schema doesn't support characters field: {schema_error}")
            logger.info(f"💾 Storing {len(characters)} characters in window storage for later use")
            
            # Return without characters (backward compatible)
            response = ComicScriptResponse(
                panels=panels,
                raw_script=script_text
            )
            
            # ✅ Store characters separately for frontend access
            # Frontend can access via global variable if needed
            return response
            
    except Exception as e:
        logger.error(f"❌ Failed to generate comic script: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate comic script: {str(e)}")

@router.post("/generate-panel-image")
async def generate_panel_image(
    request: ImageGenerationRequest,
    current_teacher: User = Depends(get_current_teacher)
):
    """Step 3: Generate image for a single comic panel (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} generating panel image")

        # ✅ Get characters from request (now properly supported in schema)
        characters = request.characters or []

        if characters:
            logger.info(f"✅ Using {len(characters)} character references for consistency")
            for char in characters:
                logger.info(f"   - {char.get('name', 'Unknown')}: {char.get('role', 'N/A')}")
        else:
            logger.warning("⚠️ No character references provided - consistency may vary")

        # ✅ Pass characters to service for consistent character rendering
        image_data = await comfyui_service.generate_image(request, characters=characters)
        
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=panel_{request.panel.id}.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@router.post("/save-module")
async def save_module(
    request: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Manually save module to database (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} saving module")
        
        classic_text = request.get('classic_text')
        modern_text = request.get('modern_text')
        comic_script = request.get('comic_script')
        panels_data = request.get('panels', [])
        
        panels = [ComicPanel(**p) for p in panels_data]
        
        module_id = db_service.create_module(classic_text, modern_text, comic_script)
        db_service.save_panels(module_id, panels)
        
        logger.info(f"Module {module_id} saved by teacher {current_teacher.username}")
        
        return {
            "success": True,
            "module_id": module_id,
            "message": f"Module saved successfully with {len(panels)} panels",
            "panel_count": len(panels),
            "created_by": current_teacher.username
        }
    except Exception as e:
        logger.error(f"Failed to save module: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save module: {str(e)}")

@router.post("/save-exercises")
async def save_exercises_to_module(
    request: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Manually save exercises to existing module (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} saving exercises")
        
        module_id = request.get('module_id')
        exercises_data = request.get('exercises', [])
        
        exercises = [Exercise(**e) for e in exercises_data]
        
        db_service.save_exercises(module_id, exercises)
        
        return {
            "success": True,
            "message": f"Saved {len(exercises)} exercises to module",
            "exercise_count": len(exercises),
            "saved_by": current_teacher.username
        }
    except Exception as e:
        logger.error(f"Failed to save exercises: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save exercises: {str(e)}")

@router.delete("/{module_id}")
async def delete_module(
    module_id: str,
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a module (TEACHER ONLY)"""
    try:
        logger.info(f"Teacher {current_teacher.username} deleting module {module_id}")
        
        success = db_service.delete_module(module_id)
        if not success:
            raise HTTPException(status_code=404, detail="Module not found")
        
        return {
            "message": "Module deleted successfully",
            "deleted_by": current_teacher.username
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete module: {str(e)}")
    
@router.post("/save-panel-audios")
async def save_panel_audios(
    request: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Save audio files for comic panels (TEACHER ONLY)
    
    Request body:
    {
        "module_id": "xxx",
        "audios": [
            {
                "panel_id": 1,
                "dialogue_audio": "data:audio/mpeg;base64,xxx",
                "narration_audio": "data:audio/mpeg;base64,xxx"
            }
        ]
    }
    """
    try:
        logger.info(f"Teacher {current_teacher.username} saving panel audios")
        
        module_id = request.get('module_id')
        audios_data = request.get('audios', [])
        
        if not module_id:
            raise HTTPException(status_code=400, detail="module_id is required")
        
        # Save each audio to database
        saved_count = 0
        for audio_data in audios_data:
            panel_id = audio_data.get('panel_id')
            dialogue_audio = audio_data.get('dialogue_audio')
            narration_audio = audio_data.get('narration_audio')
            
            # Save to database
            db_service.save_panel_audio(
                module_id=module_id,
                panel_id=panel_id,
                dialogue_audio=dialogue_audio,
                narration_audio=narration_audio
            )
            saved_count += 1
        
        logger.info(f"✅ Saved {saved_count} panel audios for module {module_id}")
        
        return {
            "success": True,
            "message": f"Saved audio for {saved_count} panels",
            "module_id": module_id,
            "saved_by": current_teacher.username
        }
        
    except Exception as e:
        logger.error(f"Failed to save panel audios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save audios: {str(e)}")


@router.get("/panel-audio/{module_id}/{panel_id}")
async def get_panel_audio(
    module_id: str,
    panel_id: int,
    audio_type: str = Query(..., description="dialogue or narration")
):
    """
    Get audio file for a specific panel (PUBLIC)
    
    Args:
        module_id: Module ID
        panel_id: Panel ID
        audio_type: 'dialogue' or 'narration'
    
    Returns:
        Audio file as MP3 stream
    """
    try:
        logger.info(f"Fetching {audio_type} audio for panel {panel_id} in module {module_id}")
        
        # Get audio from database
        audio_data = db_service.get_panel_audio(module_id, panel_id, audio_type)
        
        if not audio_data:
            raise HTTPException(status_code=404, detail="Audio not found")
        
        # If stored as base64, decode it
        if audio_data.startswith('data:audio'):
            # Remove data:audio/mpeg;base64, prefix
            audio_data = audio_data.split(',')[1]
        
        audio_bytes = base64.b64decode(audio_data)
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=panel_{panel_id}_{audio_type}.mp3",
                "Cache-Control": "public, max-age=86400"  # Cache 24 hours
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get panel audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio: {str(e)}")
    
# ============================================================================
# EXERCISE EDITING ENDPOINTS
# ============================================================================

@router.get("/{module_id}/exercises")
async def get_module_exercises(
    module_id: str,
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all exercises for a module (for editing)"""
    try:
        with db_session:
            from app.database.models import Exercise
            
            module = LearningModule.get(id=module_id)
            if not module:
                raise HTTPException(404, "Module not found")
            
            # Verify teacher owns this module
            if hasattr(module, 'created_by') and module.created_by:
                if module.created_by.id != current_teacher.id:
                    raise HTTPException(403, "You can only view exercises from your own modules")
            
            exercises = []
            
            for exercise in module.exercises:
                try:
                    # Count attempts
                    attempts_count = 0
                    try:
                        all_answers = UserAnswer.select()
                        for answer in all_answers:
                            if answer.exercise and answer.exercise.id == exercise.id:
                                attempts_count += 1
                    except Exception as count_error:
                        logger.warning(f"Could not count attempts: {count_error}")
                        attempts_count = 0
                    
                    # ✅ Options is already JSON/dict type in database
                    options = exercise.options if exercise.options else []
                    
                    # ✅ correct_answer is integer (index) in database
                    correct_answer = exercise.correct_answer
                    
                    exercises.append({
                        'id': exercise.id,
                        'question': exercise.question or '',
                        'type': exercise.type or 'multiple_choice',
                        'difficulty': exercise.difficulty or 'medium',  # ✅ ADD difficulty
                        'options': options,  # Already list/dict
                        'correct_answer': correct_answer,  # Integer index
                        'explanation': exercise.explanation or '',
                        'attempts_count': attempts_count,
                        'can_delete': attempts_count == 0
                    })
                    
                except Exception as ex:
                    logger.error(f"Error processing exercise {exercise.id}: {ex}", exc_info=True)
                    continue
            
            logger.info(f"✅ Returning {len(exercises)} exercises for module {module_id}")
            
            return {
                'module_id': module_id,
                'exercises': exercises,
                'total_exercises': len(exercises)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exercises: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get exercises: {str(e)}")


@router.post("/{module_id}/exercises")
async def add_exercise_to_module(
    module_id: str,
    exercise_data: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Add a new exercise to existing module"""
    try:
        logger.info(f"📝 Adding exercise to module {module_id}")
        logger.info(f"Received data: {exercise_data}")
        
        with db_session:
            from app.database.models import Exercise
            import time
            
            module = LearningModule.get(id=module_id)
            if not module:
                raise HTTPException(404, "Module not found")
            
            # Verify ownership
            if hasattr(module, 'created_by') and module.created_by:
                if module.created_by.id != current_teacher.id:
                    raise HTTPException(403, "You can only add exercises to your own modules")
            
            # Validate required fields
            if 'question' not in exercise_data or not exercise_data['question']:
                raise HTTPException(400, "Question is required")
            if 'type' not in exercise_data or not exercise_data['type']:
                raise HTTPException(400, "Type is required")
            if 'correct_answer' not in exercise_data:
                raise HTTPException(400, "Correct answer is required")
            if 'options' not in exercise_data:
                raise HTTPException(400, "Options are required")
            
            # ✅ Generate unique string ID
            exercise_id = f"ex_{module_id}_{int(time.time() * 1000)}"
            
            # ✅ Options - keep as list (Json field in database)
            options = exercise_data['options']
            if not isinstance(options, list):
                raise HTTPException(400, "Options must be a list")
            
            # ✅ Convert correct_answer to integer index
            correct_answer = exercise_data['correct_answer']
            if isinstance(correct_answer, str):
                # If answer is text, find index in options
                try:
                    correct_answer = options.index(correct_answer)
                except ValueError:
                    # If not found, try to parse as integer
                    try:
                        correct_answer = int(correct_answer)
                    except:
                        raise HTTPException(400, "Correct answer must be index or match an option")
            elif not isinstance(correct_answer, int):
                raise HTTPException(400, "Correct answer must be integer or string")
            
            # Validate index
            if correct_answer < 0 or correct_answer >= len(options):
                raise HTTPException(400, f"Correct answer index {correct_answer} out of range")
            
            logger.info(f"Creating exercise with ID: {exercise_id}")
            logger.info(f"Options: {options}")
            logger.info(f"Correct answer index: {correct_answer}")
            
            # ✅ Create exercise with proper types
            new_exercise = Exercise(
                id=exercise_id,
                module=module,
                type=exercise_data['type'],
                difficulty=exercise_data.get('difficulty', 'medium'),  # ✅ ADD difficulty
                question=exercise_data['question'],
                options=options,  # List/dict - Json field
                correct_answer=correct_answer,  # Integer
                explanation=exercise_data.get('explanation', ''),
                classic_text=exercise_data.get('classic_text'),
                modern_text=exercise_data.get('modern_text'),
                comic_reference=exercise_data.get('comic_reference'),
                audio_text=exercise_data.get('audio_text'),
                audio_type=exercise_data.get('audio_type'),
                grammar_rule=exercise_data.get('grammar_rule')
            )
            
            commit()
            
            logger.info(f"✅ Exercise created with ID: {new_exercise.id}")
            
            return {
                'success': True,
                'message': 'Exercise added successfully',
                'exercise': {
                    'id': new_exercise.id,
                    'question': new_exercise.question,
                    'type': new_exercise.type,
                    'options': new_exercise.options,
                    'correct_answer': new_exercise.correct_answer,
                    'explanation': new_exercise.explanation
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding exercise: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to add exercise: {str(e)}")


@router.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: str,
    exercise_data: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Update an existing exercise"""
    try:
        logger.info(f"📝 Updating exercise {exercise_id}")
        logger.info(f"Update data: {exercise_data}")
        
        with db_session:
            from app.database.models import Exercise
            
            exercise = Exercise.get(id=exercise_id)
            if not exercise:
                raise HTTPException(404, "Exercise not found")
            
            # Verify ownership
            module = exercise.module
            if hasattr(module, 'created_by') and module.created_by:
                if module.created_by.id != current_teacher.id:
                    raise HTTPException(403, "You can only edit your own modules")
            
            # Update fields
            if 'question' in exercise_data:
                exercise.question = exercise_data['question']
            
            if 'type' in exercise_data:
                exercise.type = exercise_data['type']
            
            if 'explanation' in exercise_data:
                exercise.explanation = exercise_data['explanation']
            
            # ✅ Update options first (before correct_answer)
            if 'options' in exercise_data:
                options = exercise_data['options']
                if not isinstance(options, list):
                    raise HTTPException(400, "Options must be a list")
                exercise.options = options
                logger.info(f"Updated options: {options}")
            
            # ✅ Update correct_answer with better matching
            if 'correct_answer' in exercise_data:
                correct_answer = exercise_data['correct_answer']
                logger.info(f"Processing correct_answer: '{correct_answer}' (type: {type(correct_answer).__name__})")
                
                # Get current options (either just updated or existing)
                current_options = exercise.options if hasattr(exercise, 'options') else []
                logger.info(f"Current options: {current_options}")
                
                # Convert to integer index
                if isinstance(correct_answer, int):
                    # Already an index
                    answer_index = correct_answer
                elif isinstance(correct_answer, str):
                    # Try to find exact match (case-sensitive)
                    try:
                        answer_index = current_options.index(correct_answer)
                        logger.info(f"✅ Found exact match at index {answer_index}")
                    except ValueError:
                        # Try case-insensitive match
                        answer_lower = correct_answer.lower().strip()
                        answer_index = -1
                        
                        for idx, opt in enumerate(current_options):
                            if opt.lower().strip() == answer_lower:
                                answer_index = idx
                                logger.info(f"✅ Found case-insensitive match at index {idx}")
                                break
                        
                        if answer_index == -1:
                            # Try to parse as integer string
                            try:
                                answer_index = int(correct_answer)
                                logger.info(f"✅ Parsed as integer: {answer_index}")
                            except ValueError:
                                # Last resort: show helpful error
                                logger.error(f"❌ Could not find '{correct_answer}' in options: {current_options}")
                                raise HTTPException(
                                    400, 
                                    f"Correct answer '{correct_answer}' not found in options: {current_options}"
                                )
                else:
                    raise HTTPException(400, f"Correct answer must be string or integer, got {type(correct_answer)}")
                
                # Validate index range
                if answer_index < 0 or answer_index >= len(current_options):
                    raise HTTPException(
                        400, 
                        f"Correct answer index {answer_index} out of range (options: {len(current_options)})"
                    )
                
                exercise.correct_answer = answer_index
                logger.info(f"✅ Set correct_answer to index: {answer_index} ('{current_options[answer_index]}')")
            
            commit()
            
            logger.info(f"✅ Exercise {exercise_id} updated successfully")
            
            return {
                'success': True,
                'message': 'Exercise updated successfully',
                'exercise': {
                    'id': exercise.id,
                    'question': exercise.question,
                    'type': exercise.type,
                    'options': exercise.options,
                    'correct_answer': exercise.correct_answer,
                    'explanation': exercise.explanation
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating exercise: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update exercise: {str(e)}")
    

@router.delete("/{module_id}")
async def delete_module(
    module_id: str,
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a learning module (TEACHER ONLY)"""
    try:
       # VVV GANTI INI VVV
        logger.error("!!!!!!!!!! TES KODE BARU VERSI 456 (ERROR) !!!!!!!!!!!") 
        # ^^^ GANTI INI ^^^

        logger.info(f"🗑️ Attempting to delete module: {module_id}")
        
        with db_session:
            module = LearningModule.get(id=module_id)
            if not module:
                raise HTTPException(404, "Module not found")
            
            # Verify teacher owns this module
            if hasattr(module, 'created_by') and module.created_by:
                if module.created_by.id != current_teacher.id:
                    raise HTTPException(403, "You can only delete your own modules")
            
            # ✅ Check if students have attempted this module
            students_attempted = 0
            try:
                for progress in module.user_progress:
                    # ✅ CORRECT: Use "answers" (as defined in model)
                    if progress.answers.count() > 0:
                        students_attempted += 1
            except Exception as check_error:
                logger.warning(f"Could not check attempts: {check_error}")
            
            if students_attempted > 0:
                logger.warning(f"Cannot delete module: {students_attempted} students attempted")
                raise HTTPException(
                    403, 
                    f"Cannot delete module: {students_attempted} student(s) have already attempted it"
                )
            
            logger.info(f"Module has no student attempts, proceeding with deletion...")
            
            # ✅ Delete in correct order (to respect foreign keys)
            try:
                # 1. Delete all UserAnswer records
                deleted_answers = 0
                for exercise in module.exercises:
                    for answer in exercise.user_answers:
                        answer.delete()
                        deleted_answers += 1
                
                logger.info(f"Deleted {deleted_answers} user answers")
                
                # 2. Delete all UserProgress records
                deleted_progress = 0
                for progress in module.user_progress:
                    progress.delete()
                    deleted_progress += 1
                
                logger.info(f"Deleted {deleted_progress} progress records")
                
                # 3. Delete all Exercises
                deleted_exercises = 0
                for exercise in module.exercises:
                    exercise.delete()
                    deleted_exercises += 1
                
                logger.info(f"Deleted {deleted_exercises} exercises")
                
                # 4. Delete all ComicPanels
                deleted_panels = 0
                for panel in module.panels:
                    panel.delete()
                    deleted_panels += 1
                
                logger.info(f"Deleted {deleted_panels} comic panels")
                
                # 5. Finally delete the module itself
                module.delete()
                
                # Commit all changes
                commit()
                
                logger.info(f"✅ Module {module_id} deleted successfully")
                
                return {
                    'success': True,
                    'message': 'Module deleted successfully',
                    'deleted': {
                        'answers': deleted_answers,
                        'progress': deleted_progress,
                        'exercises': deleted_exercises,
                        'panels': deleted_panels
                    }
                }
                
            except Exception as delete_error:
                logger.error(f"❌ Error during deletion: {delete_error}", exc_info=True)
                # Transaction will automatically rollback on exception
                raise HTTPException(500, f"Failed to delete module: {str(delete_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting module: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete module: {str(e)}")
    

@router.delete("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: str,
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete an exercise (only if no students attempted it)"""
    try:
        logger.info(f"🗑️ Attempting to delete exercise: {exercise_id}")
        
        with db_session:
            from app.database.models import Exercise
            
            exercise = Exercise.get(id=exercise_id)
            if not exercise:
                raise HTTPException(404, "Exercise not found")
            
            # Verify ownership
            module = exercise.module
            if hasattr(module, 'created_by') and module.created_by:
                if module.created_by.id != current_teacher.id:
                    raise HTTPException(403, "You can only delete exercises from your own modules")
            
            # ✅ Count attempts (via exercise.user_answers)
            answers_count = 0
            try:
                # Exercise.user_answers is correct relationship name
                for answer in exercise.user_answers:
                    answers_count += 1
                
                logger.info(f"Exercise has {answers_count} student attempts")
                
            except Exception as count_error:
                logger.warning(f"Could not count attempts: {count_error}")
                answers_count = 0
            
            if answers_count > 0:
                logger.warning(f"Cannot delete: {answers_count} attempts exist")
                return {
                    'success': False,
                    'message': f'Cannot delete exercise: {answers_count} students have already attempted it',
                    'can_delete': False
                }
            
            # Delete exercise
            exercise.delete()
            commit()
            
            logger.info(f"✅ Exercise {exercise_id} deleted successfully")
            
            return {
                'success': True,
                'message': 'Exercise deleted successfully'
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting exercise: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete exercise: {str(e)}")