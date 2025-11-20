# user_management.py - User Management Routes
from fastapi import APIRouter, HTTPException, Depends, Query
from pony.orm import db_session, select, desc, count
from datetime import datetime
from typing import List, Optional
import logging

from app.database.models import User, UserProgress, LearningModule
from app.routers.auth import get_current_user_from_token
from app.models.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["User Management"])

def get_current_teacher(current_user: User = Depends(get_current_user_from_token)):
    """Ensure current user is a teacher"""
    if current_user.role != 'teacher':
        raise HTTPException(403, "Only teachers can access user management")
    return current_user

# ============================================================================
# UPDATED list_users function in user_management.py
# Replace the existing list_users function (line 22-109)
# ============================================================================

@router.get("/list")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    activity_filter: Optional[str] = None,  # ✅ NEW: 'active', 'inactive_7d', 'inactive_30d'
    sort_by: str = Query("created_at", regex="^(created_at|username|full_name|last_active|login_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    List all users with pagination, filtering, and activity tracking
    
    NEW Filters:
    - activity_filter: 'active' (active in last 24h), 'inactive_7d', 'inactive_30d'
    
    NEW Sort Options:
    - last_active: Sort by last activity time
    - login_count: Sort by number of logins
    """
    try:
        with db_session:
            # ✅ FIX: Get ALL users as list first (Python 3.13 compatible)
            all_users = list(User.select())
            
            # Apply filters manually using Python
            filtered_users = all_users
            
            # Search filter
            if search:
                search_lower = search.lower()
                filtered_users = [
                    u for u in filtered_users
                    if (search_lower in u.username.lower() or
                        search_lower in u.full_name.lower() or
                        search_lower in u.email.lower())
                ]
            
            # Role filter
            if role_filter and role_filter in ['teacher', 'student']:
                filtered_users = [u for u in filtered_users if u.role == role_filter]
            
            # Status filter
            if status_filter == 'active':
                filtered_users = [u for u in filtered_users if u.is_active]
            elif status_filter == 'inactive':
                filtered_users = [u for u in filtered_users if not u.is_active]
            
            # ✅ NEW: Activity filter
            if activity_filter:
                from datetime import timedelta
                now = datetime.now()
                
                if activity_filter == 'active':
                    # Active in last 24 hours
                    cutoff = now - timedelta(hours=24)
                    filtered_users = [
                        u for u in filtered_users 
                        if u.last_active and u.last_active >= cutoff
                    ]
                elif activity_filter == 'inactive_7d':
                    # Not active in last 7 days
                    cutoff = now - timedelta(days=7)
                    filtered_users = [
                        u for u in filtered_users 
                        if not u.last_active or u.last_active < cutoff
                    ]
                elif activity_filter == 'inactive_30d':
                    # Not active in last 30 days
                    cutoff = now - timedelta(days=30)
                    filtered_users = [
                        u for u in filtered_users 
                        if not u.last_active or u.last_active < cutoff
                    ]
            
            total_count = len(filtered_users)
            
            # Sorting
            if sort_by == 'username':
                filtered_users.sort(key=lambda u: u.username.lower())
            elif sort_by == 'full_name':
                filtered_users.sort(key=lambda u: u.full_name.lower())
            elif sort_by == 'last_active':
                # ✅ NEW: Sort by last activity
                filtered_users.sort(key=lambda u: u.last_active or datetime.min)
            elif sort_by == 'login_count':
                # ✅ NEW: Sort by login count
                filtered_users.sort(key=lambda u: u.login_count or 0)
            else:  # created_at (default)
                filtered_users.sort(key=lambda u: u.created_at)
            
            # Apply sort order
            if sort_order == 'desc':
                filtered_users.reverse()
            
            # Pagination
            offset = (page - 1) * limit
            paginated_users = filtered_users[offset:offset + limit]
            
            # Build response
            users_data = []
            for user in paginated_users:
                # Get user statistics
                progress_list = list(user.progress_records)
                
                # Count completed modules
                modules_completed = sum(1 for p in progress_list if p.completed)
                total_score = sum(p.total_score for p in progress_list)
                
                # ✅ NEW: Calculate activity status
                activity_status = "never"
                if user.last_active:
                    time_diff = datetime.now() - user.last_active
                    if time_diff.total_seconds() < 3600:  # < 1 hour
                        activity_status = "online"
                    elif time_diff.total_seconds() < 86400:  # < 24 hours
                        activity_status = "today"
                    elif time_diff.days < 7:
                        activity_status = "this_week"
                    elif time_diff.days < 30:
                        activity_status = "this_month"
                    else:
                        activity_status = "inactive"
                
                users_data.append({
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    # ✅ NEW: Activity tracking fields
                    "last_active": user.last_active.isoformat() if user.last_active else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "login_count": user.login_count or 0,
                    "activity_status": activity_status,
                    # Statistics
                    "statistics": {
                        "modules_completed": modules_completed,
                        "total_score": total_score
                    }
                })
            
            return {
                "users": users_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to list users: {str(e)}")

# ============================================================================
# CHANGES MADE:
# 1. Added activity_filter parameter (active, inactive_7d, inactive_30d)
# 2. Added last_active and login_count to sort options
# 3. Response now includes last_active, last_login, login_count
# 4. Added activity_status field (online, today, this_week, this_month, inactive, never)
# ============================================================================

@router.get("/{user_id}")
async def get_user_detail(
    user_id: int,
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed information about a specific user"""
    try:
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Get progress records
            progress_records = list(user.progress_records.select())
            
            # Calculate statistics
            total_modules = len(progress_records)
            completed_modules = sum(1 for p in progress_records if p.completed)
            total_score = sum(p.total_score for p in progress_records)
            total_questions = sum(p.total_questions for p in progress_records)
            correct_answers = sum(p.correct_answers for p in progress_records)
            
            accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # Get recent activity
            recent_progress = []
            for prog in progress_records[:5]:  # Last 5 activities
                recent_progress.append({
                    "module_id": prog.module.id,
                    "module_title": prog.module.classic_text[:100] + "...",
                    "completed": prog.completed,
                    "score": prog.total_score,
                    "accuracy": (prog.correct_answers / prog.total_questions * 100) if prog.total_questions > 0 else 0,
                    "started_at": prog.started_at.isoformat(),
                    "completed_at": prog.completed_at.isoformat() if prog.completed_at else None
                })
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                },
                "statistics": {
                    "total_modules": total_modules,
                    "completed_modules": completed_modules,
                    "total_score": total_score,
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "accuracy": round(accuracy, 1)
                },
                "recent_activity": recent_progress
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        raise HTTPException(500, f"Failed to get user detail: {str(e)}")
    
# ============================================================================
# ADD THIS ENDPOINT TO user_management.py
# Add after the @router.get("/{user_id}") endpoint (around line 160)
# ============================================================================

@router.get("/{user_id}/progress")
async def get_user_progress(
    user_id: int,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get detailed progress for a specific user
    Accessible by: Teachers (any student) or Students (themselves only)
    """
    try:
        with db_session:
            # Check if user exists
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Permission check: Teachers can view anyone, students can only view themselves
            if current_user.role == 'student' and current_user.id != user_id:
                raise HTTPException(403, "You can only view your own progress")
            
            # ✅ FIX: Convert to list to avoid Python 3.13 loop issues
            progress_list = list(user.progress_records)
            
            # Build progress data
            progress_data = []
            for prog in progress_list:
                progress_data.append({
                    'id': prog.id,
                    'module_id': prog.module.id,
                    'started_at': prog.started_at.isoformat() if prog.started_at else None,
                    'completed_at': prog.completed_at.isoformat() if prog.completed_at else None,
                    'completed': prog.completed,
                    'total_score': prog.total_score,
                    'total_questions': prog.total_questions,
                    'correct_answers': prog.correct_answers
                })
            
            return {
                'user_id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'progress': progress_data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(500, f"Failed to get user progress: {str(e)}")

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    update_data: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Update user information"""
    try:
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Prevent teachers from modifying other teachers
            if user.role == 'teacher' and user.id != current_teacher.id:
                raise HTTPException(403, "Cannot modify other teacher accounts")
            
            # Update allowed fields
            if 'full_name' in update_data:
                user.full_name = update_data['full_name']
            
            if 'email' in update_data:
                # Check if email already exists
                existing = User.get(email=update_data['email'])
                if existing and existing.id != user_id:
                    raise HTTPException(400, "Email already in use")
                user.email = update_data['email']
            
            if 'is_active' in update_data:
                user.is_active = update_data['is_active']
            
            if 'role' in update_data and update_data['role'] in ['teacher', 'student']:
                # Only allow role changes for students
                if user.role == 'teacher':
                    raise HTTPException(403, "Cannot change role of teacher accounts")
                user.role = update_data['role']
            
            return {
                "success": True,
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(500, f"Failed to update user: {str(e)}")

@router.post("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_teacher: User = Depends(get_current_teacher)
):
    """Toggle user active/inactive status"""
    try:
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Prevent deactivating teacher accounts
            if user.role == 'teacher':
                raise HTTPException(403, "Cannot deactivate teacher accounts")
            
            # Prevent self-deactivation
            if user.id == current_teacher.id:
                raise HTTPException(403, "Cannot deactivate your own account")
            
            user.is_active = not user.is_active
            
            return {
                "success": True,
                "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
                "is_active": user.is_active
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        raise HTTPException(500, f"Failed to toggle user status: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a user and all their data"""
    try:
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Prevent deleting teacher accounts
            if user.role == 'teacher':
                raise HTTPException(403, "Cannot delete teacher accounts")
            
            # Prevent self-deletion
            if user.id == current_teacher.id:
                raise HTTPException(403, "Cannot delete your own account")
            
            # Delete user progress and answers
            for progress in user.progress_records:
                for answer in progress.answers:
                    answer.delete()
                progress.delete()
            
            # Delete the user
            username = user.username
            user.delete()
            
            return {
                "success": True,
                "message": f"User '{username}' and all related data deleted successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(500, f"Failed to delete user: {str(e)}")

from datetime import datetime, timedelta

from datetime import datetime, timedelta

# ============================================================================
# FIX: get_users_statistics function for Python 3.13 compatibility
# Replace the function in user_management.py (line 302-340)
# ============================================================================

@router.get("/statistics/overview")
async def get_users_statistics(
    current_teacher: User = Depends(get_current_teacher)
):
    """Get overall user statistics"""
    try:
        with db_session:
            # ✅ FIX: Get all data as lists first to avoid Python 3.13 loop bug
            all_users = list(User.select())
            all_progress = list(UserProgress.select())
            
            # Count users
            total_users = len(all_users)
            total_teachers = sum(1 for u in all_users if u.role == 'teacher')
            total_students = sum(1 for u in all_users if u.role == 'student')
            active_users = sum(1 for u in all_users if u.is_active)
            inactive_users = sum(1 for u in all_users if not u.is_active)
            
            # Count progress
            total_progress = len(all_progress)
            completed_progress = sum(1 for p in all_progress if p.completed)
            
            # ✅ FIX: Recent registrations - calculate manually
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_registrations = sum(
                1 for u in all_users 
                if u.created_at and u.created_at >= thirty_days_ago
            )
            
            # Calculate completion rate
            completion_rate = 0
            if total_progress > 0:
                completion_rate = round((completed_progress / total_progress * 100), 1)
            
            return {
                "user_counts": {
                    "total": total_users,
                    "teachers": total_teachers,
                    "students": total_students,
                    "active": active_users,
                    "inactive": inactive_users
                },
                "activity_stats": {
                    "total_module_attempts": total_progress,
                    "completed_modules": completed_progress,
                    "completion_rate": completion_rate
                },
                "recent_registrations": recent_registrations
            }
            
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# ============================================================================
# KEY CHANGES:
# 1. Get all_users = list(User.select()) FIRST
# 2. Get all_progress = list(UserProgress.select()) FIRST
# 3. Use Python's sum() and list comprehension instead of Pony's .select(lambda)
# 4. This avoids the Python 3.13 bytecode compatibility issue
# ============================================================================

@router.post("/{user_id}/reset-progress")
async def reset_user_progress(
    user_id: int,
    current_teacher: User = Depends(get_current_teacher)
):
    """Reset all progress for a specific user"""
    try:
        with db_session:
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(404, "User not found")
            
            # Delete all progress records
            progress_count = 0
            for progress in user.progress_records:
                # Delete all answers first
                for answer in progress.answers:
                    answer.delete()
                progress.delete()
                progress_count += 1
            
            return {
                "success": True,
                "message": f"Reset {progress_count} progress records for user '{user.username}'"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting user progress: {e}")
        raise HTTPException(500, f"Failed to reset progress: {str(e)}")