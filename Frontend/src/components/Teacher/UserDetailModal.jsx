import React, { useState } from 'react';
import { 
  X, User, Mail, Calendar, Trophy, Target, TrendingUp, 
  Edit, Save, RefreshCw, BookOpen 
} from 'lucide-react';

export default function UserDetailModal({ user, onClose, onUpdate, onResetProgress }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    full_name: user.user.full_name,
    email: user.user.email,
    role: user.user.role
  });

  const handleSave = () => {
    onUpdate(user.user.id, editData);
    setIsEditing(false);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>User Details</h2>
          <button className="btn-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          {/* User Info Section */}
          <div className="user-detail-section">
            <div className="user-detail-header">
              <div className="user-avatar-large">
                {user.user.full_name.charAt(0).toUpperCase()}
              </div>
              <div className="user-detail-info">
                {isEditing ? (
                  <>
                    <input
                      type="text"
                      value={editData.full_name}
                      onChange={(e) => setEditData({...editData, full_name: e.target.value})}
                      className="form-input"
                      placeholder="Full Name"
                    />
                    <input
                      type="email"
                      value={editData.email}
                      onChange={(e) => setEditData({...editData, email: e.target.value})}
                      className="form-input"
                      placeholder="Email"
                    />
                    <select
                      value={editData.role}
                      onChange={(e) => setEditData({...editData, role: e.target.value})}
                      className="form-select"
                      disabled={user.user.role === 'teacher'}
                    >
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                    </select>
                  </>
                ) : (
                  <>
                    <h3>{user.user.full_name}</h3>
                    <p className="user-username">@{user.user.username}</p>
                    <p className="user-email">{user.user.email}</p>
                    <span className={`role-badge ${user.user.role}`}>
                      {user.user.role}
                    </span>
                  </>
                )}
              </div>
              <div className="user-detail-actions">
                {isEditing ? (
                  <>
                    <button onClick={handleSave} className="btn btn-primary">
                      <Save size={16} />
                      Save
                    </button>
                    <button onClick={() => setIsEditing(false)} className="btn btn-secondary">
                      Cancel
                    </button>
                  </>
                ) : (
                  <button onClick={() => setIsEditing(true)} className="btn btn-secondary">
                    <Edit size={16} />
                    Edit
                  </button>
                )}
              </div>
            </div>

            <div className="user-meta-info">
              <div className="meta-item">
                <Calendar size={16} />
                <span>Joined: {formatDate(user.user.created_at)}</span>
              </div>
              <div className="meta-item">
                <span className={`status-indicator ${user.user.is_active ? 'active' : 'inactive'}`}></span>
                <span>Status: {user.user.is_active ? 'Active' : 'Inactive'}</span>
              </div>
            </div>
          </div>

          {/* Statistics Section */}
          <div className="user-statistics-section">
            <h4>Learning Statistics</h4>
            <div className="stats-grid">
              <div className="stat-box">
                <div className="stat-icon">
                  <BookOpen size={24} color="#667eea" />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{user.statistics.total_modules}</div>
                  <div className="stat-label">Modules Started</div>
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-icon">
                  <Target size={24} color="#28a745" />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{user.statistics.completed_modules}</div>
                  <div className="stat-label">Completed</div>
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-icon">
                  <Trophy size={24} color="#ffc107" />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{user.statistics.total_score}</div>
                  <div className="stat-label">Total Score</div>
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-icon">
                  <TrendingUp size={24} color="#dc3545" />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{user.statistics.accuracy}%</div>
                  <div className="stat-label">Accuracy</div>
                </div>
              </div>
            </div>

            <div className="question-stats">
              <p>
                Answered <strong>{user.statistics.correct_answers}</strong> out of{' '}
                <strong>{user.statistics.total_questions}</strong> questions correctly
              </p>
            </div>
          </div>

          {/* Recent Activity */}
          {user.recent_activity && user.recent_activity.length > 0 && (
            <div className="recent-activity-section">
              <h4>Recent Activity</h4>
              <div className="activity-list">
                {user.recent_activity.map((activity, index) => (
                  <div key={index} className="activity-item">
                    <div className="activity-icon">
                      <BookOpen size={20} />
                    </div>
                    <div className="activity-content">
                      <div className="activity-title">
                        Module: {activity.module_id.replace('module_', '')}
                      </div>
                      <div className="activity-details">
                        <span className={`status-badge ${activity.completed ? 'completed' : 'in-progress'}`}>
                          {activity.completed ? 'Completed' : 'In Progress'}
                        </span>
                        <span>Score: <strong>{activity.score}</strong></span>
                        <span>Accuracy: <strong>{activity.accuracy.toFixed(0)}%</strong></span>
                      </div>
                      <div className="activity-time">
                        Started: {new Date(activity.started_at).toLocaleDateString()}
                        {activity.completed_at && (
                          <> • Completed: {new Date(activity.completed_at).toLocaleDateString()}</>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="modal-actions">
            {user.user.role !== 'teacher' && (
              <button 
                onClick={() => onResetProgress(user.user.id)}
                className="btn btn-danger"
              >
                <RefreshCw size={16} />
                Reset All Progress
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}