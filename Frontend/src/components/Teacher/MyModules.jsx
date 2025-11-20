import React, { useState, useEffect } from 'react';
import { Eye, Trash2, Edit3, BookOpen, Calendar } from 'lucide-react';
import { moduleAPI, trainingAPI } from '../../services/api';
import ExerciseEditor from '../ModuleCreator/ExerciseEditor';
import '../../styles/MyModules.css';

export default function MyModules() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // ✅ Exercise Editor States
  const [showExerciseEditor, setShowExerciseEditor] = useState(false);
  const [selectedModuleId, setSelectedModuleId] = useState(null);

  useEffect(() => {
    loadModules();
  }, []);

  const loadModules = async () => {
    setLoading(true);
    try {
      const result = await moduleAPI.listModules(50);

      setModules(result.modules || []);
    } catch (error) {
      console.error('Failed to load modules:', error);
      alert('Failed to load modules: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewModule = async (moduleId) => {
    try {
      const module = await moduleAPI.getModule(moduleId);
      alert(`Module: ${moduleId}\nPanels: ${module.panels?.length || 0}\nExercises: ${module.exercises?.length || 0}`);
    } catch (error) {
      alert('Failed to load module: ' + error.message);
    }
  };

  // ✅ ADD THIS FUNCTION
  const handleEditExercises = (moduleId) => {
    console.log('📝 Opening Exercise Editor for module:', moduleId);
    setSelectedModuleId(moduleId);
    setShowExerciseEditor(true);
  };

  const handleDeleteModule = async (moduleId) => {
    if (!confirm('Are you sure you want to delete this module? This cannot be undone.')) {
      return;
    }

    try {
      await moduleAPI.deleteModule(moduleId);
      alert('✅ Module deleted successfully!');
      loadModules();
    } catch (error) {
      alert('Failed to delete module: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Loading your modules...</p>
      </div>
    );
  }

  return (
    <div className="my-modules-container">
      <div className="section-header">
        <BookOpen size={28} />
        <h2>My Created Modules</h2>
      </div>

      {modules.length > 0 ? (
        <div className="modules-grid">
          {modules.map(module => (
            <div key={module.id} className="module-card">
              <div className="module-header">
  <div>
    <h3 style={{ fontSize: '18px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
      <BookOpen size={20} color="#4a4ae6" />
      {module.module_name 
        ? `📘 ${module.module_name}` 
        : `Module ${module.id.replace('module_', '')}`}
    </h3>
    <small style={{ color: '#666', marginLeft: '28px' }}>
      ID: {module.id}
    </small>
  </div>
  <span className="module-date">
    <Calendar size={14} />
    {new Date(module.created_at).toLocaleDateString()}
  </span>
</div>


              <div className="module-preview">
                <p>{module.classic_text?.substring(0, 150)}...</p>
              </div>

              <div className="module-stats">
                <div className="stat-item">
                  <span className="stat-label">Panels:</span>
                  <span className="stat-value">{module.panel_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Exercises:</span>
                  <span className="stat-value">{module.exercise_count || 0}</span>
                </div>
              </div>

              {/* ✅ UPDATED: Add Edit Exercises Button */}
              <div className="module-actions">
                <button 
                  onClick={() => handleViewModule(module.id)}
                  className="btn btn-secondary"
                  title="View module details"
                >
                  <Eye size={16} />
                  View
                </button>
                
                {/* ✅ NEW: Edit Exercises Button */}
                <button 
                  onClick={() => handleEditExercises(module.id)}
                  className="btn btn-primary"
                  title="Edit exercises"
                >
                  <Edit3 size={16} />
                  Edit Exercises
                </button>
                
                <button 
                  onClick={() => handleDeleteModule(module.id)}
                  className="btn btn-danger"
                  title="Delete module"
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <BookOpen size={80} color="#ccc" />
          <h3>No Modules Yet</h3>
          <p>Create your first module in the "Create Module" tab</p>
        </div>
      )}

      {/* ✅ Exercise Editor Modal */}
      {showExerciseEditor && selectedModuleId && (
        <ExerciseEditor
          moduleId={selectedModuleId}
          onClose={() => {
            setShowExerciseEditor(false);
            setSelectedModuleId(null);
            loadModules(); // Refresh to update exercise count
          }}
        />
      )}
    </div>
  );
}