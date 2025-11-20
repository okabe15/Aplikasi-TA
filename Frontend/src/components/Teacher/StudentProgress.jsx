import React, { useState, useEffect } from 'react';
import { Users, Trophy, Target, TrendingUp, Eye, ArrowLeft, Award, BookOpen, CheckCircle, Clock } from 'lucide-react';
import { progressAPI, moduleAPI } from '../../services/api'; // ✅ CHANGED: use progressAPI
import StudentDetailModal from './StudentDetailModal'; // ✅ ADD: Import modal


export default function StudentProgress() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStudents();
  }, []);

  // ✅ UPDATED: Use progressAPI.getAllStudentProgress()
 const loadStudents = async () => {
  setLoading(true);
  setError(null);
  try {
    console.log('📊 Loading student progress...');
    
    const data = await progressAPI.getAllStudentProgress();
    
    console.log('✅ Received data:', data);
    console.log('Students array:', data.students);
    console.log('Students count:', data.students?.length);
    
    if (!data || !data.students) {
      console.error('❌ Invalid response format:', data);
      throw new Error('Invalid response format from server');
    }
    
    console.log('🎯 Mapping students...');
    const studentsWithProgress = data.students.map((student, index) => {
      console.log(`  - Student ${index + 1}:`, student);
      return {
        student_id: student.user_id,
        full_name: student.full_name,
        username: student.username,
        email: student.email || '',
        total_score: student.total_score || 0,
        modules_completed: student.modules_completed || 0,
        total_modules: student.total_attempts || 0,
        accuracy: student.accuracy || 0,
        latest_activity: student.latest_activity ? new Date(student.latest_activity) : null,
        rank: student.rank || (index + 1)
      };
    });
    
    console.log('✅ Mapped students:', studentsWithProgress);
    setStudents(studentsWithProgress);
    
  } catch (error) {
    console.error('❌ Failed to load students:', error);
    setError(error.message || 'Failed to load student progress. Please try again.');
  } finally {
    setLoading(false);
  }
};


  // ✅ ADD: Handler for modal
  const handleViewDetails = (student) => {
    setSelectedStudent({
      user_id: student.student_id,
      full_name: student.full_name,
      username: student.username,
      total_score: student.total_score,
      modules_completed: student.modules_completed,
      accuracy: student.accuracy,
      total_attempts: student.total_modules,
      latest_activity: student.latest_activity?.toISOString(),
      rank: student.rank
    });
  };

  // ✅ ADD: Close modal
  const closeModal = () => {
    setSelectedStudent(null);
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 80) return '#28a745';
    if (accuracy >= 60) return '#ffc107';
    return '#dc3545';
  };

  const getAccuracyLabel = (accuracy) => {
    if (accuracy >= 80) return 'Excellent';
    if (accuracy >= 60) return 'Good';
    return 'Needs Practice';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading student progress...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">
          <h3>⚠️ Error</h3>
          <p>{error}</p>
          <button onClick={loadStudents} className="btn btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // ✅ REMOVED: Student Detail View (now handled by modal)
  // Students Overview
  return (
    <div className="student-progress">
      <div className="section-header">
        <Users size={28} />
        <h2>Monitor Student Progress</h2>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#667eea'}}>
            <Users size={32} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-number">{students.length}</div>
            <div className="stat-label">Total Students</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#ffc107'}}>
            <Trophy size={32} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-number">
              {students.reduce((sum, s) => sum + s.modules_completed, 0)}
            </div>
            <div className="stat-label">Total Completions</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#28a745'}}>
            <TrendingUp size={32} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-number">
              {students.length > 0 
                ? Math.round(students.reduce((sum, s) => sum + s.accuracy, 0) / students.length)
                : 0}%
            </div>
            <div className="stat-label">Average Accuracy</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#17a2b8'}}>
            <BookOpen size={32} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-number">
              {students.reduce((sum, s) => sum + s.total_modules, 0)}
            </div>
            <div className="stat-label">Total Attempts</div>
          </div>
        </div>
      </div>

      {students.length > 0 ? (
        <div className="students-table-container">
          <table className="students-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Student</th>
                <th>Total Score</th>
                <th>Modules</th>
                <th>Accuracy</th>
                <th>Latest Activity</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student, index) => (
                <tr key={student.student_id}>
                  <td>
                    <div className="rank-badge">
                      <strong>#{index + 1}</strong>
                      {index === 0 && <span className="medal">🥇</span>}
                      {index === 1 && <span className="medal">🥈</span>}
                      {index === 2 && <span className="medal">🥉</span>}
                    </div>
                  </td>
                  <td>
                    <div className="student-cell">
                      <div className="student-avatar-small">
                        {student.full_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <strong>{student.full_name}</strong>
                        <small style={{display: 'block', color: '#666'}}>
                          @{student.username}
                        </small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <strong style={{color: '#ffc107', fontSize: '18px'}}>
                      {student.total_score}
                    </strong>
                  </td>
                  <td>
                    <span className="badge badge-info">
                      {student.modules_completed}/{student.total_modules}
                    </span>
                  </td>
                  <td>
                    <span 
                      className="accuracy-badge"
                      style={{
                        background: getAccuracyColor(student.accuracy) + '20',
                        color: getAccuracyColor(student.accuracy),
                        border: `2px solid ${getAccuracyColor(student.accuracy)}`,
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontWeight: 'bold',
                        display: 'inline-block'
                      }}
                    >
                      {student.accuracy}%
                    </span>
                  </td>
                  <td>
                    <small style={{color: '#666'}}>
                      {student.latest_activity 
                        ? new Date(student.latest_activity).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })
                        : 'No activity'}
                    </small>
                  </td>
                  <td>
                    {/* ✅ UPDATED: Use modal instead of detail view */}
                    <button 
                      onClick={() => handleViewDetails(student)}
                      className="btn btn-sm btn-primary"
                    >
                      <Eye size={14} />
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <Users size={80} color="#ccc" />
          <h3>No Students Found</h3>
          <p>Students will appear here once they register and start completing modules</p>
        </div>
      )}

      {/* ✅ ADD: Modal */}
      {selectedStudent && (
        <StudentDetailModal 
          student={selectedStudent}
          onClose={closeModal}
        />
      )}
    </div>
  );
}