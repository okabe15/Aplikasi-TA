import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, BookOpen, Plus, List, User, Users, TrendingUp, Shield, FileText } from 'lucide-react';
import ClassicTextInput from './ModuleCreator/ClassicTextInput';
import ModernTextDisplay from './ModuleCreator/ModernTextDisplay';
import ComicScriptDisplay from './ModuleCreator/ComicScriptDisplay';
import ComicPanelResult from './ModuleCreator/ComicPanelResult';
import TrainingMode from './Training/TrainingMode';
import Loading from './common/Loading';
import MyModules from './Teacher/MyModules';
import StudentProgress from './Teacher/StudentProgress';
import UserManagement from './Teacher/UserManagement';
import Reports from './Teacher/Reports';
import { moduleAPI, trainingAPI } from '../services/api';
import '../styles/Dashboard.css';
import '../styles/UserManagement.css';

export default function TeacherDashboard() {
  const navigate = useNavigate();

  // ✅ FIX: Replace AuthContext with localStorage
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  // ✅ UPDATE: Add 'progress' and 'users' views
  const [view, setView] = useState('create'); // 'create', 'modules', 'progress', or 'users'

  const [modules, setModules] = useState([]);

  // Comic generation states (PRESERVED)
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const [classicText, setClassicText] = useState('');
  const [modernText, setModernText] = useState('');
  const [comicScript, setComicScript] = useState(null);
  const [panels, setPanels] = useState([]);
  const [panelImages, setPanelImages] = useState([]);
  const [mode, setMode] = useState('generator');

  useEffect(() => {
    if (view === 'modules') {
      loadModules();
    }
  }, [view]);

  const loadModules = async () => {
    try {
      const result = await moduleAPI.listModules(50);
      setModules(result.modules || []);
    } catch (error) {
      console.error('Failed to load modules:', error);
    }
  };

  // ✅ PRESERVED: All existing functions
  const handleModernizeText = async (text) => {
    setClassicText(text);
    setLoading(true);
    setLoadingMessage('AI is modernizing the classic text...');

    try {
      const result = await moduleAPI.modernizeText(text);
      setModernText(result.modern_text);
      setStep(2);
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateComic = async () => {
    setLoading(true);
    setLoadingMessage('AI is creating comic script...');

    try {
      const result = await moduleAPI.generateComicScript({
        original_text: classicText,
        modern_text: modernText
      });

      setComicScript(result);
      setPanels(result.panels);
      setStep(3);
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePanels = async () => {
    setLoading(true);
    const images = [];
    const base64Images = [];

    try {
      for (let i = 0; i < panels.length; i++) {
        setLoadingMessage(`Generating panel ${i + 1}/${panels.length}...`);

        const panelRequest = {
          panel: panels[i],
          width: 512,
          height: 512,
          steps: 25,
          cfg: 7.5,
          negative_prompt: "blurry, low quality, distorted, ugly, bad anatomy, watermark, signature, text errors, illegible text, garbled text, modern clothing, anachronistic elements, bubble, multiple characters"
        };

        const imageBlob = await moduleAPI.generatePanelImage(panelRequest);
        const base64String = await moduleAPI.blobToBase64(imageBlob);
        const imageUrl = URL.createObjectURL(imageBlob);

        images.push({
          panel: panels[i],
          imageUrl: imageUrl
        });

        base64Images.push({
          panel_id: panels[i].id,
          image_base64: base64String
        });
      }

      setPanelImages(images);
      window.savedBase64Images = base64Images;
      setStep(4);
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayAudio = async (text, voiceType) => {
    try {
      const audioUrl = await moduleAPI.generateAudio(text, voiceType);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('Audio playback error:', error);
    }
  };

  const switchToTraining = () => {
    if (!classicText || !modernText || panels.length === 0) {
      alert('Please generate a complete comic first before accessing training mode.');
      return;
    }
    setMode('training');
  };

  const switchToGenerator = () => {
    setMode('generator');
  };

  const handleStartOver = () => {
    setStep(1);
    setClassicText('');
    setModernText('');
    setComicScript(null);
    setPanels([]);
    setPanelImages([]);
    setMode('generator');
  };

  const canAccessTraining = classicText && modernText && panels.length > 0;

  return (
    <div className="dashboard-container">
      {/* Header (PRESERVED) */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <BookOpen size={32} color="#667eea" />
            <div>
              <h1>Teacher Dashboard</h1>
              <p>Create Interactive Learning Modules</p>
            </div>
          </div>
          <div className="header-right">
            <div className="user-info">
              <User size={20} />
              <span>{user?.full_name || user?.username || 'Teacher'}</span>
              <span className="role-badge teacher">Teacher</span>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* ✅ UPDATED Navigation: Added Student Progress */}
      <nav className="dashboard-nav">
        <button
          className={`nav-btn ${view === 'create' ? 'active' : ''}`}
          onClick={() => setView('create')}
        >
          <Plus size={20} />
          Create Module
        </button>
        <button
          className={`nav-btn ${view === 'modules' ? 'active' : ''}`}
          onClick={() => setView('modules')}
        >
          <List size={20} />
          My Modules ({modules.length})
        </button>
        {/* ✅ NEW: Student Progress Tab */}
        <button
          className={`nav-btn ${view === 'progress' ? 'active' : ''}`}
          onClick={() => setView('progress')}
        >
          <Users size={20} />
          Student Progress
        </button>
        {/* ✅ NEW: User Management Tab */}
        <button
          className={`nav-btn ${view === 'users' ? 'active' : ''}`}
          onClick={() => setView('users')}
        >
          <Shield size={20} />
          User Management
        </button>

        {/* ✅ NEW: Reports Tab */}
        <button
          className={`nav-btn ${view === 'reports' ? 'active' : ''}`}
          onClick={() => setView('reports')}
        >
          <FileText size={20} />
          Reports
        </button>
      </nav>

      {/* Content (PRESERVED + ADDED) */}
      <div className="dashboard-content">
        {/* ✅ UPDATED: My Modules View - Use MyModules Component */}
        {view === 'modules' ? (
          <div className="modules-section">
            <MyModules />
          </div>
        ) : view === 'progress' ? (
          /* ✅ NEW: Student Progress View */
          <div className="progress-section">
            <StudentProgress />
          </div>
        ) : view === 'users' ? (
          /* ✅ NEW: User Management View */
          <div className="user-management-section">
            <UserManagement />
          </div>

        ) : view === 'reports' ? (
          /* ✅ NEW: Reports View */
          <div className="reports-section">
            <Reports />
          </div>
        ) : (
          /* ✅ PRESERVED: Create Module View (Original Code) */
          <>
            {loading && <Loading message={loadingMessage} />}

            {mode === 'generator' ? (
              <>
                {/* ✅ PRESERVED: Workflow Indicator */}
                <div className="workflow-indicator">
                  {[1, 2, 3, 4].map(num => (
                    <div
                      key={num}
                      className={`step ${step === num ? 'active' : step > num ? 'completed' : ''}`}
                    >
                      <div className="step-number">{num}</div>
                      <div className="step-label">
                        {num === 1 && 'Input Text'}
                        {num === 2 && 'Modernize'}
                        {num === 3 && 'Comic Script'}
                        {num === 4 && 'Generate Images'}
                      </div>
                    </div>
                  ))}
                </div>

                {/* ✅ PRESERVED: Step 1 - Classic Text Input */}
                {step >= 1 && !loading && (
                  <ClassicTextInput
                    onSubmit={handleModernizeText}
                    loading={loading}
                  />
                )}

                {/* ✅ PRESERVED: Step 2 - Modern Text Display */}
                {step >= 2 && modernText && !loading && (
                  <ModernTextDisplay
                    originalText={classicText}
                    modernText={modernText}
                    onEdit={() => {
                      setStep(1);
                      setModernText('');
                      setComicScript(null);
                      setPanels([]);
                      setPanelImages([]);
                    }}
                    onGenerateComic={handleGenerateComic}
                    onPlayAudio={handlePlayAudio}
                    loading={loading}
                  />
                )}

                {/* ✅ PRESERVED: Step 3 - Comic Script */}
                {step >= 3 && comicScript && !loading && (
                  <ComicScriptDisplay
                    script={comicScript}
                    onGeneratePanels={handleGeneratePanels}
                    loading={loading}
                  />
                )}

                {/* ✅ PRESERVED: Step 4 - Panel Results */}
                {step >= 4 && panelImages.length > 0 && (
                  <div className="result-section">
                    <ComicPanelResult
                      panels={panelImages}
                      onPlayAudio={handlePlayAudio}
                    />

                    <div className="result-actions">
                      <button
                        onClick={switchToTraining}
                        className="btn btn-success"
                      >
                        🎓 Start Training & Save
                      </button>

                      <button onClick={handleStartOver} className="btn btn-secondary">
                        🔄 Create New Comic
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              /* ✅ PRESERVED: Training Mode */
              <TrainingMode
                classicText={classicText}
                modernText={modernText}
                comicScript={comicScript}
                panels={panels}
                onBack={switchToGenerator}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}