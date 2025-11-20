# ============================================================================
# leaderboard.py - NEW ROUTER for Leaderboard Functionality
# Add this as a new file: app/routers/leaderboard.py
# ============================================================================

from fastapi import APIRouter, HTTPException, Depends, Query
from pony.orm import db_session, select, desc
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.database.models import User, UserProgress, LearningModule
from app.routers.auth import get_current_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])

@router.get("/")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    timeframe: str = Query("all_time", regex="^(all_time|this_week|this_month)$"),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get student leaderboard ranked by total score
    
    Parameters:
    - limit: Number of top students to return (default 10)
    - timeframe: 'all_time', 'this_week', or 'this_month' (default 'all_time')
    
    ✅ STUDENT ONLY: Only shows students in ranking
    """
    try:
        with db_session:
            # Get all users and progress as lists first (Python 3.13 compatible)
            all_users = list(User.select())
            all_progress = list(UserProgress.select())
            
            # Filter only students
            students = [u for u in all_users if u.role == 'student']
            
            # Calculate time filter
            now = datetime.now()
            start_date = None
            
            if timeframe == 'this_week':
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == 'this_month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # else: all_time, no filter
            
            # Build leaderboard data
            leaderboard_data = []
            
            for student in students:
                # Get student's progress records
                student_progress = [p for p in all_progress if p.user.id == student.id]
                
                # Filter by timeframe if specified
                if start_date:
                    student_progress = [
                        p for p in student_progress 
                        if p.started_at >= start_date
                    ]
                
                # Skip if no progress
                if not student_progress:
                    continue
                
                # Calculate statistics
                total_score = sum(p.total_score for p in student_progress)
                completed_modules = sum(1 for p in student_progress if p.completed)
                total_questions = sum(p.total_questions for p in student_progress)
                correct_answers = sum(p.correct_answers for p in student_progress)
                
                # Calculate accuracy
                accuracy = 0
                if total_questions > 0:
                    accuracy = round((correct_answers / total_questions) * 100, 2)
                
                # Determine badges
                badges = []
                if completed_modules >= 10:
                    badges.append('🏆 Master Learner')
                elif completed_modules >= 5:
                    badges.append('📚 Dedicated Student')
                elif completed_modules >= 1:
                    badges.append('🌟 First Steps')
                
                if accuracy >= 90:
                    badges.append('🎯 Perfect Accuracy')
                elif accuracy >= 80:
                    badges.append('✨ High Achiever')
                
                if total_score >= 1000:
                    badges.append('💎 Score Champion')
                elif total_score >= 500:
                    badges.append('⭐ Rising Star')
                
                # Get latest activity
                latest_activity = None
                if student_progress:
                    dates = [p.completed_at if p.completed_at else p.started_at for p in student_progress]
                    dates = [d for d in dates if d is not None]
                    if dates:
                        latest_activity = max(dates)
                
                leaderboard_data.append({
                    'student_id': student.id,
                    'username': student.username,
                    'student_name': student.full_name,
                    'total_score': total_score,
                    'modules_completed': completed_modules,
                    'accuracy': accuracy,
                    'badges': badges,
                    'latest_activity': latest_activity.isoformat() if latest_activity else None,
                    'is_current_user': student.id == current_user.id
                })
            
            # Sort by total score (highest first)
            leaderboard_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Add rank
            for rank, entry in enumerate(leaderboard_data, start=1):
                entry['rank'] = rank
            
            # Apply limit
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
                'time_period': timeframe,
                'generated_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error generating leaderboard: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate leaderboard: {str(e)}")


@router.get("/student/{student_id}")
async def get_student_rank(
    student_id: int,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get specific student's rank and position in leaderboard
    
    Accessible by: Teachers (any student) or Students (themselves only)
    """
    try:
        with db_session:
            # Check if student exists
            student = User.get(id=student_id)
            if not student or student.role != 'student':
                raise HTTPException(404, "Student not found")
            
            # Permission check
            if current_user.role == 'student' and current_user.id != student_id:
                raise HTTPException(403, "You can only view your own rank")
            
            # Get all students and their scores
            all_users = list(User.select())
            all_progress = list(UserProgress.select())
            
            students = [u for u in all_users if u.role == 'student']
            
            # Calculate scores for all students
            student_scores = []
            for s in students:
                s_progress = [p for p in all_progress if p.user.id == s.id]
                total_score = sum(p.total_score for p in s_progress)
                student_scores.append({
                    'user_id': s.id,
                    'username': s.username,
                    'total_score': total_score
                })
            
            # Sort by score
            student_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Find current student's rank
            rank = None
            above_me = []
            below_me = []
            
            for idx, entry in enumerate(student_scores, start=1):
                if entry['user_id'] == student_id:
                    rank = idx
                    # Get 3 students above
                    above_me = student_scores[max(0, idx-4):idx-1]
                    # Get 3 students below
                    below_me = student_scores[idx:idx+3]
                    break
            
            # Get detailed student progress
            student_progress = [p for p in all_progress if p.user.id == student_id]
            total_score = sum(p.total_score for p in student_progress)
            completed_modules = sum(1 for p in student_progress if p.completed)
            
            return {
                'student_id': student_id,
                'username': student.username,
                'full_name': student.full_name,
                'rank': rank,
                'total_score': total_score,
                'completed_modules': completed_modules,
                'total_students': len(students),
                'percentile': round((1 - (rank - 1) / len(students)) * 100) if rank else 0,
                'students_above': above_me,
                'students_below': below_me
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student rank: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get student rank: {str(e)}")


@router.get("/top-performers")
async def get_top_performers(
    metric: str = Query('score', regex='^(score|accuracy|modules)$'),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get top performing students by different metrics
    
    Parameters:
    - metric: 'score', 'accuracy', or 'modules'
    - limit: Number of students to return
    
    Accessible by: Teachers only
    """
    try:
        # Only teachers can view this
        if current_user.role != 'teacher':
            raise HTTPException(403, "Only teachers can view top performers")
        
        with db_session:
            all_users = list(User.select())
            all_progress = list(UserProgress.select())
            
            students = [u for u in all_users if u.role == 'student']
            
            performers = []
            
            for student in students:
                s_progress = [p for p in all_progress if p.user.id == student.id]
                
                if not s_progress:
                    continue
                
                total_score = sum(p.total_score for p in s_progress)
                completed_modules = sum(1 for p in s_progress if p.completed)
                
                # Calculate accuracy
                total_accuracy = 0
                count_with_questions = 0
                for p in s_progress:
                    if p.total_questions > 0:
                        total_accuracy += (p.correct_answers / p.total_questions) * 100
                        count_with_questions += 1
                
                avg_accuracy = round(total_accuracy / count_with_questions) if count_with_questions > 0 else 0
                
                performers.append({
                    'user_id': student.id,
                    'username': student.username,
                    'full_name': student.full_name,
                    'total_score': total_score,
                    'modules_completed': completed_modules,
                    'accuracy': avg_accuracy
                })
            
            # Sort by selected metric
            if metric == 'score':
                performers.sort(key=lambda x: x['total_score'], reverse=True)
            elif metric == 'accuracy':
                performers.sort(key=lambda x: x['accuracy'], reverse=True)
            elif metric == 'modules':
                performers.sort(key=lambda x: x['modules_completed'], reverse=True)
            
            # Add rank
            for rank, entry in enumerate(performers[:limit], start=1):
                entry['rank'] = rank
            
            return {
                'metric': metric,
                'top_performers': performers[:limit],
                'generated_at': datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top performers: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get top performers: {str(e)}")

# ============================================================================
# REGISTER THIS ROUTER IN main.py
# ============================================================================
# 
# In app/main.py, add:
# 
# from app.routers import leaderboard
# app.include_router(leaderboard.router)
#
# ============================================================================