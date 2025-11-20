# reports.py - COMPLETE Report Generation API Endpoints
import io
import json
from pony.orm import db_session
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response, JSONResponse  # ✅ ADD JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List
from app.routers.auth import get_current_user_from_token
from app.database.models import User, UserProgress
from app.services.report_service import report_service
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def get_current_teacher(current_user: User = Depends(get_current_user_from_token)):
    """Ensure current user is a teacher"""
    if current_user.role != 'teacher':
        raise HTTPException(403, "Only teachers can generate reports")
    return current_user

@router.get("/types")
async def get_report_types(current_teacher: User = Depends(get_current_teacher)):
    """Get available report types"""
    return {
        "report_types": [
            {
                "id": "student_progress",
                "name": "Individual Student Progress Report",
                "description": "Detailed progress report for a specific student",
                "parameters": ["student_id"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "class_overview",
                "name": "Class Overview Report",
                "description": "Overview of all students' performance",
                "parameters": [],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "module_performance",
                "name": "Module Performance Report",
                "description": "Performance analysis for learning modules",
                "parameters": ["module_id (optional)"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "exercise_analysis",
                "name": "Exercise Analysis Report",
                "description": "Detailed analysis of exercise performance by type",
                "parameters": [],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "engagement_metrics",
                "name": "Student Engagement Report",
                "description": "Engagement and activity metrics",
                "parameters": ["date_from", "date_to"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "comparative_analysis",
                "name": "Comparative Analysis Report",
                "description": "Compare performance across students, modules, or time periods",
                "parameters": ["analysis_type", "entity_ids"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "achievement_summary",
                "name": "Achievement Summary Report",
                "description": "Summary of student achievements and badges",
                "parameters": ["date_from", "date_to"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "weekly_summary",
                "name": "Weekly Summary Report",
                "description": "Weekly performance summary for all students",
                "parameters": ["week_offset"],
                "formats": ["pdf", "excel", "json"]
            }
        ]
    }

@router.get("/preview/{report_type}")
async def preview_report(
    report_type: str,
    student_id: Optional[int] = Query(None),
    module_id: Optional[str] = Query(None),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get preview data for a report type"""
    try:
        # Return sample preview data based on report type
        if report_type == "student_progress":
            return {
                "report_type": report_type,
                "sample_data": {
                    "student_name": "Sample Student",
                    "total_modules": 10,
                    "completed_modules": 7,
                    "average_score": 85.5,
                    "accuracy": 78.2,
                    "top_performers": []
                }
            }
        elif report_type == "class_overview":
            return {
                "report_type": report_type,
                "sample_data": {
                    "total_students": 25,
                    "average_score": 78.5,
                    "completion_rate": 68.0,
                    "top_performers": [
                        {"name": "John Doe", "score": 95},
                        {"name": "Jane Smith", "score": 92}
                    ]
                }
            }
        else:
            return {
                "report_type": report_type,
                "sample_data": {
                    "message": "Preview data will be available soon"
                }
            }
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(500, f"Failed to generate preview: {str(e)}")

@router.get("/scheduled")
async def get_scheduled_reports(current_teacher: User = Depends(get_current_teacher)):
    """Get list of scheduled reports"""
    # For now, return empty list
    # Implement actual scheduling system later
    return {
        "scheduled_reports": []
    }

@router.post("/schedule")
async def schedule_report(
    report_type: str,
    schedule: str,
    recipients: List[str],
    parameters: dict,
    current_teacher: User = Depends(get_current_teacher)
):
    """Schedule a report for automatic generation"""
    # TODO: Implement scheduling system (e.g., using Celery + Redis)
    return {
        "success": True,
        "message": "Report scheduling feature is coming soon",
        "schedule_id": "schedule_12345"
    }

@router.post("/generate/student_progress")
async def generate_student_progress_report(
    student_id: int = Query(..., description="Student ID"),
    format: str = Query("pdf", description="Output format: pdf, excel, or json"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate individual student progress report"""
    try:
        report_data = report_service.generate_student_progress_report(student_id, format)
        
        if format == "pdf":
            return Response(
                content=report_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=student_progress_{student_id}.pdf"
                }
            )
        elif format == "excel":
            return Response(
                content=report_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=student_progress_{student_id}.xlsx"
                }
            )
        else:
            return Response(
                content=report_data,
                media_type="application/json"
            )
            
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Error generating student progress report: {e}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.post("/generate/class_overview")
async def generate_class_overview_report(
    format: str = Query("pdf", description="Output format: pdf, excel, or json"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate class overview report"""
    try:
        report_data = report_service.generate_class_overview_report(format)
        
        if format == "pdf":
            return Response(
                content=report_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=class_overview.pdf"
                }
            )
        elif format == "excel":
            return Response(
                content=report_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=class_overview.xlsx"
                }
            )
        else:
            return Response(
                content=report_data,
                media_type="application/json"
            )
            
    except Exception as e:
        logger.error(f"Error generating class overview report: {e}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.post("/generate/module_performance")
async def generate_module_performance_report(
    module_id: Optional[str] = Query(None, description="Module ID (optional - leave empty for all modules)"),
    format: str = Query("pdf", description="Output format: pdf, excel, or json"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate module performance report"""
    try:
        report_data = report_service.generate_module_performance_report(module_id, format)
        
        filename = f"module_performance_{module_id}" if module_id else "all_modules_performance"
        
        if format == "pdf":
            return Response(
                content=report_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.pdf"
                }
            )
        elif format == "excel":
            return Response(
                content=report_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.xlsx"
                }
            )
        else:
            return Response(
                content=report_data,
                media_type="application/json"
            )
            
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Error generating module performance report: {e}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.post("/generate/exercise_analysis")
async def generate_exercise_analysis_report(
    format: str = Query("pdf", description="Output format: pdf, excel, or json"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate exercise analysis report"""
    try:
        report_data = report_service.generate_exercise_analysis_report(format)
        
        if format == "pdf":
            return Response(
                content=report_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=exercise_analysis.pdf"
                }
            )
        elif format == "excel":
            return Response(
                content=report_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=exercise_analysis.xlsx"
                }
            )
        else:
            return Response(
                content=report_data,
                media_type="application/json"
            )
            
    except Exception as e:
        logger.error(f"Error generating exercise analysis report: {e}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.post("/generate/engagement_metrics")
async def generate_engagement_report(
    date_from: Optional[datetime] = Query(None, description="Start date (defaults to 30 days ago)"),
    date_to: Optional[datetime] = Query(None, description="End date (defaults to today)"),
    format: str = Query("pdf", description="Output format: pdf, excel, or json"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate student engagement metrics report"""
    try:
        report_data = report_service.generate_engagement_report(date_from, date_to, format)
        
        if format == "pdf":
            return Response(
                content=report_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=engagement_metrics.pdf"
                }
            )
        elif format == "excel":
            return Response(
                content=report_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=engagement_metrics.xlsx"
                }
            )
        else:
            return Response(
                content=report_data,
                media_type="application/json"
            )
            
    except Exception as e:
        logger.error(f"Error generating engagement report: {e}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

# ============================================================================
# COMPARATIVE ANALYSIS REPORT
# ============================================================================

@router.post("/generate/comparative_analysis")
async def generate_comparative_analysis_report(
    format: str = Query("pdf", regex="^(pdf|excel|json)$"),
    comparison_type: str = Query("students", regex="^(students|modules|time)$"),
    student_ids: Optional[str] = Query(None),
    module_ids: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate comparative analysis report"""
    try:
        with db_session:
            student_id_list = []
            module_id_list = []
            
            if student_ids:
                student_id_list = [int(id.strip()) for id in student_ids.split(',')]
            if module_ids:
                module_id_list = [id.strip() for id in module_ids.split(',')]
            
            # Get only student progress
            all_progress = list(UserProgress.select())
            all_progress = [p for p in all_progress if p.user.role == 'student']
            
            if student_id_list:
                all_progress = [p for p in all_progress if p.user.id in student_id_list]
            if module_id_list:
                all_progress = [p for p in all_progress if p.module.id in module_id_list]
            if date_from:
                start_date = datetime.fromisoformat(date_from)
                all_progress = [p for p in all_progress if p.started_at >= start_date]
            if date_to:
                end_date = datetime.fromisoformat(date_to)
                all_progress = [p for p in all_progress if p.started_at <= end_date]
            
            comparison_data = []
            
            # ============================================================
            # COMPARISON TYPE 1: BY STUDENTS
            # ============================================================
            if comparison_type == "students":
                student_data = {}
                for progress in all_progress:
                    student_id = progress.user.id
                    if student_id not in student_data:
                        student_data[student_id] = {
                            'name': progress.user.full_name,
                            'username': progress.user.username,
                            'total_score': 0,
                            'modules_completed': 0,
                            'total_questions': 0,
                            'correct_answers': 0
                        }
                    student_data[student_id]['total_score'] += progress.total_score
                    if progress.completed:
                        student_data[student_id]['modules_completed'] += 1
                    student_data[student_id]['total_questions'] += progress.total_questions
                    student_data[student_id]['correct_answers'] += progress.correct_answers
                
                for student in student_data.values():
                    if student['total_questions'] > 0:
                        student['accuracy'] = round((student['correct_answers'] / student['total_questions']) * 100, 2)
                    else:
                        student['accuracy'] = 0
                
                comparison_data = list(student_data.values())
                comparison_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            # ============================================================
            # COMPARISON TYPE 2: BY MODULES
            # ============================================================
            elif comparison_type == "modules":
                module_data = {}
                for progress in all_progress:
                    module_id = progress.module.id
                    if module_id not in module_data:
                        module_data[module_id] = {
                            'module_id': module_id,
                            'module_title': progress.module.classic_text[:100] + "...",
                            'total_attempts': 0,
                            'completed_count': 0,
                            'total_score': 0,
                            'total_questions': 0,
                            'correct_answers': 0,
                            'unique_students': set()
                        }
                    
                    module_data[module_id]['total_attempts'] += 1
                    if progress.completed:
                        module_data[module_id]['completed_count'] += 1
                    module_data[module_id]['total_score'] += progress.total_score
                    module_data[module_id]['total_questions'] += progress.total_questions
                    module_data[module_id]['correct_answers'] += progress.correct_answers
                    module_data[module_id]['unique_students'].add(progress.user.id)
                
                for module in module_data.values():
                    if module['total_questions'] > 0:
                        module['avg_accuracy'] = round((module['correct_answers'] / module['total_questions']) * 100, 2)
                    else:
                        module['avg_accuracy'] = 0
                    
                    if module['total_attempts'] > 0:
                        module['completion_rate'] = round((module['completed_count'] / module['total_attempts']) * 100, 2)
                        module['avg_score'] = round(module['total_score'] / module['total_attempts'], 2)
                    else:
                        module['completion_rate'] = 0
                        module['avg_score'] = 0
                    
                    module['student_count'] = len(module['unique_students'])
                    del module['unique_students']  # Remove set before JSON serialization
                
                comparison_data = list(module_data.values())
                comparison_data.sort(key=lambda x: x['avg_score'], reverse=True)
            
            # ============================================================
            # COMPARISON TYPE 3: BY TIME PERIODS
            # ============================================================
            elif comparison_type == "time":
                # Group by week or month
                time_data = {}
                
                for progress in all_progress:
                    # Group by week (Monday as start of week)
                    progress_date = progress.started_at
                    week_start = progress_date - timedelta(days=progress_date.weekday())
                    week_key = week_start.strftime('%Y-%m-%d')
                    
                    if week_key not in time_data:
                        time_data[week_key] = {
                            'period': week_key,
                            'week_start': week_start.strftime('%Y-%m-%d'),
                            'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
                            'total_attempts': 0,
                            'completed_count': 0,
                            'total_score': 0,
                            'total_questions': 0,
                            'correct_answers': 0,
                            'active_students': set()
                        }
                    
                    time_data[week_key]['total_attempts'] += 1
                    if progress.completed:
                        time_data[week_key]['completed_count'] += 1
                    time_data[week_key]['total_score'] += progress.total_score
                    time_data[week_key]['total_questions'] += progress.total_questions
                    time_data[week_key]['correct_answers'] += progress.correct_answers
                    time_data[week_key]['active_students'].add(progress.user.id)
                
                for period in time_data.values():
                    if period['total_questions'] > 0:
                        period['avg_accuracy'] = round((period['correct_answers'] / period['total_questions']) * 100, 2)
                    else:
                        period['avg_accuracy'] = 0
                    
                    if period['total_attempts'] > 0:
                        period['completion_rate'] = round((period['completed_count'] / period['total_attempts']) * 100, 2)
                        period['avg_score'] = round(period['total_score'] / period['total_attempts'], 2)
                    else:
                        period['completion_rate'] = 0
                        period['avg_score'] = 0
                    
                    period['student_count'] = len(period['active_students'])
                    del period['active_students']  # Remove set before JSON serialization
                
                comparison_data = list(time_data.values())
                # Sort by date
                comparison_data.sort(key=lambda x: x['period'])
            
            report_data = {
                'report_type': 'Comparative Analysis',
                'comparison_type': comparison_type,
                'generated_at': datetime.now().isoformat(),
                'data': comparison_data,
                'summary': {
                    'total_records': len(comparison_data),
                    'date_from': date_from,
                    'date_to': date_to,
                    'comparison_by': comparison_type
                }
            }
            
            if format == 'json':
                return JSONResponse(content=report_data)
            elif format == 'pdf':
                pdf_content = report_service.generate_pdf_report(report_data)
                return Response(content=pdf_content, media_type='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename=comparative_analysis.pdf'})
            else:
                excel_content = report_service.generate_excel_report(report_data)
                return Response(content=excel_content, 
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment; filename=comparative_analysis.xlsx'})
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed: {str(e)}")


# ============================================================================
# ACHIEVEMENT SUMMARY REPORT
# ============================================================================

@router.post("/generate/achievement_summary")
async def generate_achievement_summary_report(
    format: str = Query("pdf", regex="^(pdf|excel|json)$"),
    student_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate achievement summary report"""
    try:
        with db_session:
            if student_id:
                all_users = [User.get(id=student_id)]
                if not all_users[0]:
                    raise HTTPException(404, "Student not found")
            else:
                all_users = list(User.select())
                all_users = [u for u in all_users if u.role == 'student']
            
            achievements_data = []
            
            for user in all_users:
                progress_list = list(user.progress_records)
                
                if date_from:
                    start_date = datetime.fromisoformat(date_from)
                    progress_list = [p for p in progress_list if p.started_at >= start_date]
                if date_to:
                    end_date = datetime.fromisoformat(date_to)
                    progress_list = [p for p in progress_list if p.started_at <= end_date]
                
                total_score = sum(p.total_score for p in progress_list)
                modules_completed = sum(1 for p in progress_list if p.completed)
                total_questions = sum(p.total_questions for p in progress_list)
                correct_answers = sum(p.correct_answers for p in progress_list)
                
                avg_accuracy = 0
                if total_questions > 0:
                    avg_accuracy = round((correct_answers / total_questions) * 100, 2)
                
                badges = []
                if modules_completed >= 10:
                    badges.append('🏆 Master Learner')
                elif modules_completed >= 5:
                    badges.append('📚 Dedicated Student')
                elif modules_completed >= 1:
                    badges.append('🌟 First Steps')
                
                if avg_accuracy >= 90:
                    badges.append('🎯 Perfect Accuracy')
                elif avg_accuracy >= 80:
                    badges.append('✨ High Achiever')
                
                if total_score >= 1000:
                    badges.append('💎 Score Champion')
                elif total_score >= 500:
                    badges.append('⭐ Rising Star')
                
                # ✅ FIX: Convert datetime to ISO string immediately
                first_module_date = None
                latest_activity_date = None
                
                if progress_list:
                    first_module_date = progress_list[0].started_at.isoformat()
                    latest_dates = [p.completed_at or p.started_at for p in progress_list]
                    if latest_dates:
                        latest_activity_date = max(latest_dates).isoformat()
                
                achievements_data.append({
                    'student_id': user.id,
                    'student_name': user.full_name,
                    'total_score': total_score,
                    'modules_completed': modules_completed,
                    'accuracy': avg_accuracy,
                    'badges': badges,
                    'milestones': {
                        'first_module': first_module_date,  # ✅ Already ISO string
                        'latest_activity': latest_activity_date,  # ✅ Already ISO string
                        'best_score': max((p.total_score for p in progress_list), default=0)
                    }
                })
            
            achievements_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            report_data = {
                'report_type': 'Achievement Summary',
                'generated_at': datetime.now().isoformat(),  # ✅ Already ISO string
                'students': achievements_data,
                'summary': {
                    'total_students': len(achievements_data), 
                    'date_from': date_from, 
                    'date_to': date_to
                }
            }
            
            # ✅ FIX: Handle format properly
            if format == 'json':
                # ✅ Use StreamingResponse for file download
                json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
                filename = f"achievement_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                return StreamingResponse(
                    io.BytesIO(json_str.encode('utf-8')),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            
            elif format == 'pdf':
                pdf_content = report_service.generate_pdf_report(report_data)
                filename = f"achievement_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return Response(
                    content=pdf_content, 
                    media_type='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename={filename}'}
                )
            
            else:  # excel
                excel_content = report_service.generate_excel_report(report_data)
                filename = f"achievement_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return Response(
                    content=excel_content,
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': f'attachment; filename={filename}'}
                )
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed: {str(e)}")


# ============================================================================
# WEEKLY SUMMARY REPORT
# ============================================================================

@router.post("/generate/weekly_summary")
async def generate_weekly_summary_report(
    format: str = Query("pdf", regex="^(pdf|excel|json)$"),
    week_offset: int = Query(0),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate weekly summary report"""
    try:
        with db_session:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=7)
            
            # ✅ FIX: Convert to list first, then filter
            all_progress = list(UserProgress.select())
            all_progress = [p for p in all_progress if p.user.role == 'student']
            week_progress = [p for p in all_progress if week_start <= p.started_at < week_end]
            
            student_summary = {}
            
            for progress in week_progress:
                student_id = progress.user.id
                if student_id not in student_summary:
                    student_summary[student_id] = {
                        'student_id': student_id,
                        'student_name': progress.user.full_name,
                        'modules_attempted': 0,
                        'modules_completed': 0,
                        'total_score': 0,
                        'total_questions': 0,
                        'correct_answers': 0,
                        'time_spent_minutes': 0
                    }
                
                student_summary[student_id]['modules_attempted'] += 1
                if progress.completed:
                    student_summary[student_id]['modules_completed'] += 1
                student_summary[student_id]['total_score'] += progress.total_score
                student_summary[student_id]['total_questions'] += progress.total_questions
                student_summary[student_id]['correct_answers'] += progress.correct_answers
                
                if progress.completed_at and progress.started_at:
                    time_diff = (progress.completed_at - progress.started_at).total_seconds() / 60
                    student_summary[student_id]['time_spent_minutes'] += int(time_diff)
            
            for student in student_summary.values():
                if student['total_questions'] > 0:
                    student['accuracy'] = round((student['correct_answers'] / student['total_questions']) * 100, 2)
                else:
                    student['accuracy'] = 0
            
            weekly_summary = {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'total_students_active': len(student_summary),
                'total_modules_attempted': sum(s['modules_attempted'] for s in student_summary.values()),
                'total_modules_completed': sum(s['modules_completed'] for s in student_summary.values()),
                'total_score': sum(s['total_score'] for s in student_summary.values()),
                'avg_accuracy': round(sum(s['accuracy'] for s in student_summary.values()) / len(student_summary) 
                    if student_summary else 0, 2)
            }
            
            report_data = {
                'report_type': 'Weekly Summary',
                'generated_at': datetime.now().isoformat(),
                'weekly_summary': weekly_summary,
                'students': list(student_summary.values())
            }
            
            if format == 'json':
                return JSONResponse(content=report_data)
            elif format == 'pdf':
                pdf_content = report_service.generate_pdf_report(report_data)
                return Response(content=pdf_content, media_type='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename=weekly_summary.pdf'})
            else:
                excel_content = report_service.generate_excel_report(report_data)
                return Response(content=excel_content,
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment; filename=weekly_summary.xlsx'})
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed: {str(e)}")