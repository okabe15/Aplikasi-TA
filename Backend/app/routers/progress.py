from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime
from pony.orm import db_session, desc, select, count, commit
import logging

from app.routers.auth import get_current_user_from_token
from app.database.models import LearningModule, User, ComicPanel, Exercise, UserProgress, UserAnswer
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/progress",
    tags=["progress"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_teacher(token: str = Depends(oauth2_scheme)):
    """Verify user is a teacher"""
    return auth_service.get_current_active_teacher(token)


@router.get("/my-progress")
@db_session
async def get_my_progress(current_user: User = Depends(get_current_user_from_token)):
    """Get current user's learning progress"""
    try:
        progress_records = list(
            UserProgress.select(lambda p: p.user.id == current_user.id)
            .order_by(desc(UserProgress.completed_at))
        )
        
        progress_list = []
        total_score = 0
        
        for progress in progress_records:
            module = progress.module
            
            progress_list.append({
                'module_id': module.id,
                'module_name': module.module_name or f"Module {module.id.replace('module_', '')}",
                'classic_text_preview': module.classic_text[:100] if module.classic_text else "",
                'completed': progress.completed,
                'started_at': progress.started_at.isoformat() if progress.started_at else None,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'total_questions': progress.total_questions,
                'correct_answers': progress.correct_answers,
                'total_score': progress.total_score
            })
            
            total_score += progress.total_score
        
        return {
            'user_id': current_user.id,
            'full_name': current_user.full_name,
            'progress': progress_list,
            'total_score': total_score
        }
        
    except Exception as e:
        logger.error(f"Failed to get user progress: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get progress: {str(e)}")


@router.get("/leaderboard")
@db_session
async def get_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get top students by total score"""
    try:
        users_with_scores = []
        
        all_users = list(User.select(lambda u: u.role == 'student'))
        
        for user in all_users:
            progress_records = list(UserProgress.select(lambda p: p.user.id == user.id))
            
            total_score = sum(p.total_score for p in progress_records)
            total_questions = sum(p.total_questions for p in progress_records)
            correct_answers = sum(p.correct_answers for p in progress_records)
            modules_completed = len([p for p in progress_records if p.completed])
            
            accuracy = round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 1)
            
            users_with_scores.append({
                'user_id': user.id,
                'full_name': user.full_name,
                'username': user.username,
                'total_score': total_score,
                'modules_completed': modules_completed,
                'accuracy': accuracy,
                'total_attempts': len(progress_records),
                'is_current_user': user.id == current_user.id
            })
        
        users_with_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        for rank, user_data in enumerate(users_with_scores, start=1):
            user_data['rank'] = rank
        
        return {
            'leaderboard': users_with_scores[:limit],
            'total_students': len(users_with_scores),
            'current_user_rank': next((u['rank'] for u in users_with_scores if u['is_current_user']), None)
        }
        
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get leaderboard: {str(e)}")


@router.get("/all-students")
@db_session
async def get_all_student_progress(
    current_teacher: User = Depends(get_current_teacher)
):
    """Get progress for all students (TEACHER ONLY)"""
    try:
        logger.info("📊 Getting all student progress...")
        students_progress = []
        
        all_students = list(User.select(lambda u: u.role == 'student'))
        logger.info(f"Found {len(all_students)} students")
        
        for user in all_students:
            try:
                progress_records = list(UserProgress.select(lambda p: p.user.id == user.id))
                
                total_score = sum(p.total_score for p in progress_records) if progress_records else 0
                total_questions = sum(p.total_questions for p in progress_records) if progress_records else 0
                correct_answers = sum(p.correct_answers for p in progress_records) if progress_records else 0
                modules_completed = len([p for p in progress_records if p.completed]) if progress_records else 0
                
                accuracy = round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 1)
                
                latest_activity = None
                if progress_records:
                    try:
                        latest_progress = max(
                            progress_records, 
                            key=lambda p: (p.completed_at or p.started_at or datetime.min)
                        )
                        latest_activity = latest_progress.completed_at or latest_progress.started_at
                    except Exception as e:
                        logger.warning(f"Could not determine latest activity: {e}")
                
                students_progress.append({
                    'user_id': user.id,
                    'full_name': user.full_name,
                    'username': user.username,
                    'total_score': total_score,
                    'modules_completed': modules_completed,
                    'accuracy': accuracy,
                    'total_attempts': len(progress_records),
                    'latest_activity': latest_activity.isoformat() if latest_activity else None
                })
                
                logger.info(f"  ✅ {user.username}: {total_score} points, {modules_completed} completed")
                
            except Exception as student_error:
                logger.error(f"Error processing student {user.username}: {student_error}")
                students_progress.append({
                    'user_id': user.id,
                    'full_name': user.full_name,
                    'username': user.username,
                    'total_score': 0,
                    'modules_completed': 0,
                    'accuracy': 0,
                    'total_attempts': 0,
                    'latest_activity': None
                })
        
        students_progress.sort(key=lambda x: x['total_score'], reverse=True)
        
        for rank, student in enumerate(students_progress, start=1):
            student['rank'] = rank
        
        logger.info(f"✅ Returning {len(students_progress)} students")
        
        response = {
            'students': students_progress,
            'total_students': len(students_progress),
            'total_completions': sum(s['modules_completed'] for s in students_progress),
            'average_accuracy': round(
                sum(s['accuracy'] for s in students_progress) / len(students_progress)
                if students_progress else 0, 1
            )
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get all student progress: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get student progress: {str(e)}")


@router.get("/student/{user_id}/details")
@db_session
async def get_student_details(
    user_id: int,
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed student progress (TEACHER ONLY)"""
    try:
        user = User.get(id=user_id)
        if not user:
            raise HTTPException(404, "Student not found")
        
        progress_records = list(
            UserProgress.select(lambda p: p.user.id == user_id)
            .order_by(desc(UserProgress.completed_at))
        )
        
        modules_data = []
        total_score = 0
        total_questions_answered = 0
        total_correct = 0
        
        for progress in progress_records:
            module = progress.module
            
            questions = []
            for i in range(progress.total_questions):
                questions.append({
                    'number': i + 1,
                    'topic': ['Tenses', 'Vocabulary', 'Grammar', 'Comprehension', 'Analysis'][i % 5],
                    'correct': i < progress.correct_answers
                })
            
            modules_data.append({
                'module_id': module.id,
                'module_name': module.module_name or f"Module {module.id.replace('module_', '')}",
                'classic_text': module.classic_text[:200] if module.classic_text else "",
                'completed': progress.completed,
                'started_at': progress.started_at.isoformat() if progress.started_at else None,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'score': progress.total_score,
                'total_questions': progress.total_questions,
                'correct_answers': progress.correct_answers,
                'time_spent': 15,
                'questions': questions
            })
            
            total_score += progress.total_score
            total_questions_answered += progress.total_questions
            total_correct += progress.correct_answers
        
        accuracy = round((total_correct / total_questions_answered * 100) if total_questions_answered > 0 else 0, 1)
        
        return {
            'user_id': user_id,
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'modules': modules_data,
            'stats': {
                'total_score': total_score,
                'total_modules': len(progress_records),
                'total_questions': total_questions_answered,
                'total_correct': total_correct,
                'accuracy': accuracy
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get student details: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get student details: {str(e)}")


@router.get("/module/{module_id}/detail")
@db_session
async def get_module_detail(
    module_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get module detail with panels and exercises"""
    try:
        module = LearningModule.get(id=module_id)
        if not module:
            raise HTTPException(404, "Module not found")
        
        panels = []
        for panel in list(module.panels.order_by(lambda p: p.panel_number)):
            panels.append({
                'id': panel.id,
                'panel_number': panel.panel_number,
                'dialogue': panel.dialogue,
                'narration': panel.narration,
                'visual': panel.visual,
                'setting': panel.setting,
                'mood': panel.mood,
                'composition': panel.composition,
                'image_base64': panel.image_base64
            })
        
        exercises = []
        for exercise in list(module.exercises):
            exercises.append({
                'id': exercise.id,
                'question_text': exercise.question,
                'options': exercise.options,
                'correct_answer': exercise.correct_answer,
                'explanation': exercise.explanation,
                'type': exercise.type
            })
        
        return {
            'id': module.id,
            'module_name': module.module_name,
            'classic_text': module.classic_text,
            'modern_text': module.modern_text,
            'comic_script': module.comic_script,
            'panels': panels,
            'exercises': exercises,
            'created_at': module.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get module detail: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get module detail: {str(e)}")


@router.get("/debug/all-users")
@db_session
async def debug_all_users(
    current_teacher: User = Depends(get_current_teacher)
):
    """Debug: Show all users with their roles"""
    try:
        all_users = list(User.select())
        
        users_info = []
        for user in all_users:
            users_info.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
            })
        
        return {
            'total_users': len(users_info),
            'users': users_info,
            'students': [u for u in users_info if u['role'] == 'student'],
            'teachers': [u for u in users_info if u['role'] == 'teacher']
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
        raise HTTPException(500, str(e))