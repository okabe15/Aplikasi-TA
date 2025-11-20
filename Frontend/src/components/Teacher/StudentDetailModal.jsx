import React, { useState, useEffect } from 'react';
import { 
  X, Download, Mail, TrendingUp, CheckCircle, 
  XCircle, Clock, Award, BookOpen, Target 
} from 'lucide-react';
import { progressAPI } from '../../services/api';


export default function StudentDetailModal({ student, onClose }) {
  const [detailedProgress, setDetailedProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  setDetailedProgress(null);
  setLoading(true);

  if (student?.user_id) loadStudentDetails();
}, [student?.user_id]);


  const loadStudentDetails = async () => {
    try {
      setLoading(true);
      const response = await progressAPI.getStudentDetails(student.user_id);
      setDetailedProgress(response);
    } catch (error) {
      console.error('Failed to load student details:', error);
      alert('Failed to load student details');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content loading" onClick={e => e.stopPropagation()}>
          <div className="spinner"></div>
          <p>Loading student details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="student-detail-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="student-info">
            <div className="student-avatar">
              {detailedProgress?.full_name?.charAt(0).toUpperCase() || 'S'}
            </div>
            <div>
              <h2>{detailedProgress?.full_name || 'Student'}</h2>
              <p className="student-email">{detailedProgress?.username}</p>
              <span className="rank-badge">🏆 Rank #{student.rank}</span>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {/* Stats Overview */}
        <div className="stats-overview">
          <div className="stat-box">
            <Award size={32} color="#ffc107" />
            <div>
              <div className="stat-number">{detailedProgress?.stats?.total_score || 0}</div>
              <div className="stat-label">Total Points</div>
            </div>
          </div>
          <div className="stat-box">
            <BookOpen size={32} color="#28a745" />
            <div>
              <div className="stat-number">{detailedProgress?.stats?.total_modules || 0}</div>
              <div className="stat-label">Modules Done</div>
            </div>
          </div>
          <div className="stat-box">
            <Target size={32} color="#667eea" />
            <div>
              <div className="stat-number">{detailedProgress?.stats?.accuracy || 0}%</div>
              <div className="stat-label">Accuracy</div>
            </div>
          </div>
          <div className="stat-box">
            <TrendingUp size={32} color="#17a2b8" />
            <div>
              <div className="stat-number">{detailedProgress?.stats?.total_correct || 0}/{detailedProgress?.stats?.total_questions || 0}</div>
              <div className="stat-label">Correct Answers</div>
            </div>
          </div>
        </div>

        {/* Module History */}
        <div className="module-history">
          <h3>📚 Module Completion History</h3>
          
          {detailedProgress?.modules?.length > 0 ? (
            detailedProgress.modules.map((module, index) => (
              <div key={index} className="module-detail-card">
                <div className="module-detail-header">
                  <div>
                    <h4>📖 {module.module_name}</h4>
                    <span className={`status-badge ${module.completed ? 'completed' : 'in-progress'}`}>
                      {module.completed ? '✅ Completed' : '⏳ In Progress'}
                    </span>
                  </div>
                  <div className="module-score">
                    <Award size={20} color="#ffc107" />
                    <strong>{module.score} points</strong>
                  </div>
                </div>

                <div className="module-meta">
                  {module.started_at && (
                    <span>📅 Started: {new Date(module.started_at).toLocaleString()}</span>
                  )}
                  {module.completed_at && (
                    <span>✅ Completed: {new Date(module.completed_at).toLocaleString()}</span>
                  )}
                  <span>⏱️ Time: {module.time_spent} minutes</span>
                  <span>🎯 Accuracy: {Math.round((module.correct_answers / module.total_questions) * 100)}%</span>
                </div>

                {/* Question Breakdown */}
                <div className="questions-breakdown">
                  <strong>Questions Answered ({module.correct_answers}/{module.total_questions}):</strong>
                  <div className="questions-list">
                    {module.questions?.map((q, qIndex) => (
                      <div key={qIndex} className="question-item">
                        {q.correct ? (
                          <CheckCircle size={16} color="#28a745" />
                        ) : (
                          <XCircle size={16} color="#dc3545" />
                        )}
                        <span>Q{q.number}: {q.topic} {q.correct ? '✓' : '✗'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Story Preview */}
                {module.classic_text && (
                  <div className="text-preview">
                    <small><strong>Story Extract:</strong> {module.classic_text}...</small>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state">
              <BookOpen size={60} color="#ccc" />
              <p>No modules completed yet</p>
            </div>
          )}
        </div>

        {/* Performance Analysis */}
        {detailedProgress?.modules?.length > 0 && (
          <div className="performance-analysis">
            <h3>🎯 Performance Analysis</h3>
            <div className="analysis-grid">
              <div className="analysis-item strengths">
                <strong>💪 Strengths:</strong>
                <ul>
                  {detailedProgress.stats.accuracy >= 90 && <li>✅ Excellent accuracy ({detailedProgress.stats.accuracy}%)</li>}
                  {detailedProgress.stats.total_modules >= 3 && <li>✅ Consistent learner</li>}
                  <li>✅ Vocabulary comprehension</li>
                </ul>
              </div>
              <div className="analysis-item improvements">
                <strong>📈 Keep Practicing:</strong>
                <ul>
                  {detailedProgress.stats.accuracy < 80 && <li>📖 Focus on accuracy</li>}
                  {detailedProgress.stats.total_modules < 3 && <li>🎯 Complete more modules</li>}
                  <li>🔄 Review incorrect answers</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="modal-actions">
          <button className="btn btn-primary" onClick={downloadReport}>
            <Download size={18} />
            Download Report
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            <X size={18} />
            Close
          </button>
        </div>
      </div>
    </div>
  );
}