// StudentDashboard.jsx - PROPER VERSION FOR STUDENTS
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LogOut, BookOpen, User, Trophy, Target, 
  TrendingUp, Eye, PlayCircle, Award, Calendar
} from 'lucide-react';
import { moduleAPI, trainingAPI } from '../services/api';
import TrainingMode from './Training/TrainingMode';
import ComicPanelResult from './ModuleCreator/ComicPanelResult';
import Leaderboard from './Student/Leaderboard';
import Loading from './common/Loading';
import '../styles/Dashboard.css';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const [view, setView] = useState('modules'); // 'modules', 'progress', 'leaderboard', 'study'
  const [modules, setModules] = useState([]);
  const [myProgress, setMyProgress] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Study mode states
  const [selectedModule, setSelectedModule] = useState(null);
  const [studyMode, setStudyMode] = useState(null); // 'view' or 'training'

  useEffect(() => {
    loadModules();
    loadMyProgress();
  }, []);

  const loadModules = async () => {
    try {
      const result = await moduleAPI.listModules(50);
      setModules(result.modules || []);
    } catch (error) {
      console.error('Failed to load modules:', error);
    }
  };

  const loadMyProgress = async () => {
    try {
      const data = await trainingAPI.getMyProgress();
      setMyProgress(data);
    } catch (error) {
      console.error('Failed to load progress:', error);
    }
  };

  const handleViewModule = async (moduleId) => {
    setLoading(true);
    try {
      const moduleData = await trainingAPI.getModuleDetail(moduleId);
      setSelectedModule(moduleData);
      setStudyMode('view');
    } catch (error) {
      alert('Failed to load module: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTraining = () => {
    if (!selectedModule) return;
    setStudyMode('training');
  };

  const handleBackToModules = () => {
    setSelectedModule(null);
    setStudyMode(null);
    setView('modules');
    loadMyProgress();
  };

  const playAudio = async (text, voiceType) => {
    try {
      const audioUrl = await moduleAPI.generateAudio(text, voiceType);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('Audio playback error:', error);
    }
  };

  // Study Mode View
  if (studyMode === 'view' && selectedModule) {
    const panelImages = selectedModule.panels.map(panel => ({
      panel: panel,
      imageUrl: panel.image_base64 || ''
    }));

    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <div className="header-content">
            <div className="header-left">
              <BookOpen size={32} color="#667eea" />
              <div>
                <h1>Studying Module</h1>
                <p>Module ID: {selectedModule.id}</p>
              </div>
            </div>
            <button onClick={handleBackToModules} className="btn btn-secondary">
              ← Back to Modules
            </button>
          </div>
        </header>

        <div className="dashboard-content">
          {loading && <Loading message="Loading module..." />}

          <div className="module-viewer">
            <div className="module-text-section">
              <h3>Classic Text</h3>
              <div className="text-content">{selectedModule.classic_text}</div>
            </div>

            <div className="module-text-section">
              <h3>Modern Text</h3>
              <div className="text-content">{selectedModule.modern_text}</div>
            </div>

            {panelImages.length > 0 && (
              <ComicPanelResult 
                panels={panelImages}
                onPlayAudio={playAudio}
              />
            )}

            <div className="study-actions">
              <button 
                onClick={handleStartTraining}
                className="btn btn-success btn-lg"
              >
                🎓 Start Training Exercises
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Training Mode
  if (studyMode === 'training' && selectedModule) {
    return (
      <div className="dashboard-container">
        <TrainingMode
          classicText={selectedModule.classic_text}
          modernText={selectedModule.modern_text}
          comicScript={selectedModule.comic_script}
          panels={selectedModule.panels}
          preloadedExercises={selectedModule.exercises}
          selectedModule={selectedModule}
          onBack={handleBackToModules}
        />
      </div>
    );
  }

  // Main Dashboard - Calculate stats
  const completedModules = myProgress?.progress?.length || 0;
  const totalScore = myProgress?.total_score || 0;
  const avgAccuracy = myProgress?.progress?.length > 0
    ? Math.round(
        myProgress.progress.reduce((sum, p) => sum + (p.correct_answers / p.total_questions * 100), 0) / 
        myProgress.progress.length
      )
    : 0;

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <BookOpen size={32} color="#667eea" />
            <div>
              <h1>Student Dashboard</h1>
              <p>Learn Classic English Through Comics</p>
            </div>
          </div>
          <div className="header-right">
            <div className="user-info">
              <User size={20} />
              <span>{user?.full_name || user?.username || 'Student'}</span>
              <span className="role-badge student">Student</span>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="dashboard-nav">
        <button
          className={`nav-btn ${view === 'modules' ? 'active' : ''}`}
          onClick={() => setView('modules')}
        >
          <BookOpen size={20} />
          Available Modules ({modules.length})
        </button>
        <button
          className={`nav-btn ${view === 'progress' ? 'active' : ''}`}
          onClick={() => setView('progress')}
        >
          <Target size={20} />
          My Progress
        </button>
        <button
          className={`nav-btn ${view === 'leaderboard' ? 'active' : ''}`}
          onClick={() => setView('leaderboard')}
        >
          <Trophy size={20} />
          Leaderboard
        </button>
      </nav>

      {/* Content */}
      <div className="dashboard-content">
        {/* Stats Cards (Always Visible) */}
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-icon" style={{background: '#667eea'}}>
              <Target size={32} color="white" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{completedModules}</div>
              <div className="stat-label">Modules Completed</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{background: '#ffc107'}}>
              <Trophy size={32} color="white" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{totalScore}</div>
              <div className="stat-label">Total Score</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{background: '#28a745'}}>
              <TrendingUp size={32} color="white" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{avgAccuracy}%</div>
              <div className="stat-label">Avg Accuracy</div>
            </div>
          </div>
          <div 
            className="stat-card clickable" 
            onClick={() => setView('leaderboard')}
            style={{cursor: 'pointer'}}
          >
            <div className="stat-icon" style={{background: '#dc3545'}}>
              <Award size={32} color="white" />
            </div>
            <div className="stat-content">
              <div className="stat-number">🏆</div>
              <div className="stat-label">Your Rank</div>
              <small style={{fontSize: '10px', color: '#64748b', marginTop: '4px'}}>
                Click to view leaderboard
              </small>
            </div>
          </div>
        </div>

        {/* Available Modules View */}
        {view === 'modules' && (
          <div className="modules-section">
            <div className="section-header">
              <BookOpen size={28} />
              <h2>Available Learning Modules</h2>
            </div>

            {modules.length > 0 ? (
              <div className="modules-grid">
                {modules.map(module => {
                  const isCompleted = myProgress?.progress?.some(p => p.module_id === module.id);
                  
                  return (
                    <div key={module.id} className="module-card">
                      <div className="module-header">
                        <h3>
  <BookOpen size={20} />
  {module.module_name || `Module ${module.id.replace('module_', '')}`}
</h3>
                        {isCompleted && (
                          <span className="badge badge-success">✅ Completed</span>
                        )}
                      </div>

                      <div className="module-preview">
                        <p>{module.classic_text.substring(0, 150)}...</p>
                      </div>

                      <div className="module-stats-grid">
                        <div className="module-stat">
                          <BookOpen size={18} color="#667eea" />
                          <div>
                            <strong>{module.panel_count}</strong>
                            <span>Panels</span>
                          </div>
                        </div>
                        <div className="module-stat">
                          <Target size={18} color="#28a745" />
                          <div>
                            <strong>{module.exercise_count}</strong>
                            <span>Exercises</span>
                          </div>
                        </div>
                        <div className="module-stat">
                          <Calendar size={18} color="#ffc107" />
                          <div>
                            <small>
                              {new Date(module.created_at).toLocaleDateString()}
                            </small>
                          </div>
                        </div>
                      </div>

                      <div className="module-actions">
                        <button 
                          onClick={() => handleViewModule(module.id)}
                          className="btn btn-primary"
                        >
                          <PlayCircle size={16} />
                          {isCompleted ? 'Study Again' : 'Start Learning'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">
                <BookOpen size={80} color="#ccc" />
                <h3>No Modules Available</h3>
                <p>Modules will appear here when teachers create them</p>
              </div>
            )}
          </div>
        )}

        {/* My Progress View */}
        {view === 'progress' && myProgress && (
          <div className="progress-section">
            <div className="section-header">
              <Target size={28} />
              <h2>My Learning Progress</h2>
            </div>

            {myProgress.progress && myProgress.progress.length > 0 ? (
              <div className="progress-list">
                {myProgress.progress.map((prog, index) => {
                  const accuracy = (prog.correct_answers / prog.total_questions * 100).toFixed(0);
                  
                  return (
                    <div key={index} className="progress-card">
                      <div className="progress-card-header">
                        <div>
                          <h4>{prog.module_name || `Module ${prog.module_id.replace('module_', '')}`}</h4>
                          <span className={`status-badge ${prog.completed ? 'completed' : 'in-progress'}`}>
                            {prog.completed ? '✅ Completed' : '⏳ In Progress'}
                          </span>
                        </div>
                        <div className="progress-score">
                          <Trophy size={20} color="#ffc107" />
                          <strong>{prog.total_score}</strong> points
                        </div>
                      </div>

                      <p className="module-preview">{prog.classic_text_preview}</p>

                      <div className="progress-stats-grid">
                        <div className="progress-stat-item">
                          <span className="stat-label">Questions</span>
                          <span className="stat-value">
                            {prog.correct_answers}/{prog.total_questions}
                          </span>
                        </div>
                        <div className="progress-stat-item">
                          <span className="stat-label">Accuracy</span>
                          <span 
                            className="stat-value"
                            style={{
                              color: accuracy >= 80 ? '#28a745' : accuracy >= 60 ? '#ffc107' : '#dc3545'
                            }}
                          >
                            {accuracy}%
                          </span>
                        </div>
                        <div className="progress-stat-item">
                          <span className="stat-label">Score</span>
                          <span className="stat-value" style={{color: '#ffc107'}}>
                            {prog.total_score}
                          </span>
                        </div>
                      </div>

                      <div className="progress-dates">
                        <small>
                          <strong>Started:</strong> {new Date(prog.started_at).toLocaleString()}
                        </small>
                        {prog.completed_at && (
                          <small>
                            <strong>Completed:</strong> {new Date(prog.completed_at).toLocaleString()}
                          </small>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">
                <Target size={80} color="#ccc" />
                <h3>No Progress Yet</h3>
                <p>Start learning modules to track your progress!</p>
                <button onClick={() => setView('modules')} className="btn btn-primary">
                  Browse Modules
                </button>
              </div>
            )}
          </div>
        )}

        {/* Leaderboard View */}
        {view === 'leaderboard' && (
          <Leaderboard />
        )}
      </div>
    </div>
  );
}