import React, { useState, useEffect } from 'react';
import { Edit3, Trash2, Plus, X, Save, ChevronDown, ChevronUp } from 'lucide-react';
import { moduleAPI } from '../../services/api';
import '../../styles/ExerciseEditor.css';

export default function ExerciseEditor({ moduleId, onClose }) {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedExercises, setExpandedExercises] = useState(new Set());
  const [showEditor, setShowEditor] = useState(false);
  const [editingExercise, setEditingExercise] = useState(null);
  const [isNewExercise, setIsNewExercise] = useState(false);

  useEffect(() => {
    loadExercises();
  }, [moduleId]);

  const loadExercises = async () => {
    setLoading(true);
    try {
      const data = await moduleAPI.getModuleExercises(moduleId);
      setExercises(data.exercises || []);
    } catch (error) {
      console.error('Failed to load exercises:', error);
      alert('Failed to load exercises: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (exerciseId) => {
    setExpandedExercises(prev => {
      const newSet = new Set(prev);
      if (newSet.has(exerciseId)) {
        newSet.delete(exerciseId);
      } else {
        newSet.add(exerciseId);
      }
      return newSet;
    });
  };

  const handleEdit = (exercise) => {
    let correctAnswerText = exercise.correct_answer;
    if (typeof exercise.correct_answer === 'number' && exercise.options) {
      correctAnswerText = exercise.options[exercise.correct_answer] || '';
    }
    
    setEditingExercise({
      ...exercise,
      correct_answer: correctAnswerText
    });
    setIsNewExercise(false);
    setShowEditor(true);
  };

  const handleAddNew = () => {
    setEditingExercise({
      question: '',
      type: 'multiple_choice',
      options: ['', '', '', ''],
      correct_answer: '',
      explanation: ''
    });
    setIsNewExercise(true);
    setShowEditor(true);
  };

  const handleSave = async () => {
    try {
      if (!editingExercise.question.trim()) {
        alert('Please enter a question');
        return;
      }

      if (editingExercise.type === 'multiple_choice') {
        const filledOptions = editingExercise.options.filter(opt => opt.trim());
        if (filledOptions.length < 2) {
          alert('Please provide at least 2 options');
          return;
        }
        if (!editingExercise.correct_answer) {
          alert('Please select the correct answer');
          return;
        }
      }

      const exerciseData = {
        question: editingExercise.question,
        type: editingExercise.type,
        options: editingExercise.options.filter(opt => opt.trim()),
        correct_answer: editingExercise.correct_answer,
        explanation: editingExercise.explanation || ''
      };

      if (isNewExercise) {
        await moduleAPI.addExercise(moduleId, exerciseData);
        alert('✅ Exercise added successfully!');
      } else {
        await moduleAPI.updateExercise(editingExercise.id, exerciseData);
        alert('✅ Exercise updated successfully!');
      }

      setShowEditor(false);
      setEditingExercise(null);
      loadExercises();
    } catch (error) {
      console.error('Failed to save exercise:', error);
      alert('Failed to save exercise: ' + error.message);
    }
  };

  const handleDelete = async (exerciseId, attemptsCount) => {
    if (attemptsCount > 0) {
      alert(`⚠️ Cannot delete this exercise!\n\n${attemptsCount} student(s) have already attempted it.\n\nYou can still EDIT the exercise to fix any issues.`);
      return;
    }

    if (!confirm('Are you sure you want to delete this exercise?')) {
      return;
    }

    try {
      const result = await moduleAPI.deleteExercise(exerciseId);
      
      if (result.success) {
        alert('✅ Exercise deleted successfully!');
        loadExercises();
      } else {
        alert(result.message || 'Cannot delete exercise');
      }
    } catch (error) {
      console.error('Failed to delete exercise:', error);
      alert('Failed to delete exercise: ' + error.message);
    }
  };

  const renderCorrectAnswerSelector = () => {
    if (!editingExercise) return null;

    if (editingExercise.type !== 'multiple_choice') {
      return (
        <input
          type="text"
          value={editingExercise.correct_answer}
          onChange={(e) => setEditingExercise({
            ...editingExercise,
            correct_answer: e.target.value
          })}
          placeholder="Enter correct answer"
          className="form-input"
        />
      );
    }

    const validOptions = editingExercise.options.filter(opt => opt.trim());
    
    return (
      <select
        value={editingExercise.correct_answer}
        onChange={(e) => setEditingExercise({
          ...editingExercise,
          correct_answer: e.target.value
        })}
        className="form-select"
        required
      >
        <option value="">-- Select Correct Answer --</option>
        {validOptions.map((option, index) => (
          <option key={index} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  };

  if (loading) {
    return (
      <div className="exercise-editor-modal">
        <div className="exercise-editor-content">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading exercises...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="exercise-editor-modal">
      <div className="exercise-editor-content">
        {/* Header with Close Button */}
        <div className="editor-main-header">
          <div>
            <h2>📝 Exercise Editor</h2>
            <p className="editor-subtitle">Module: {moduleId}</p>
          </div>
          <button onClick={onClose} className="close-button" title="Close">
            <X size={24} />
          </button>
        </div>

        {/* Exercise List View */}
        {!showEditor && (
          <div className="exercises-container">
            {/* Action Bar */}
            <div className="action-bar">
              <div className="exercise-count">
                <span className="count-badge">{exercises.length}</span>
                <span>Total Exercises</span>
              </div>
              <button onClick={handleAddNew} className="btn-add-new">
                <Plus size={20} />
                Add New Exercise
              </button>
            </div>

            {/* Exercise Cards */}
            {exercises.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📝</div>
                <h3>No Exercises Yet</h3>
                <p>Click "Add New Exercise" to create your first exercise</p>
              </div>
            ) : (
              <div className="exercises-list">
                {exercises.map((exercise, index) => {
                  const isExpanded = expandedExercises.has(exercise.id);
                  const correctAnswerText = typeof exercise.correct_answer === 'number' && exercise.options
                    ? exercise.options[exercise.correct_answer]
                    : exercise.correct_answer;

                  return (
                    <div key={exercise.id} className="exercise-item">
                      {/* Exercise Header */}
                      <div className="exercise-item-header">
                        <div className="exercise-info">
                          <div className="exercise-title">
                            <span className="exercise-number">Exercise #{index + 1}</span>
                            <span className="exercise-type-badge">{exercise.type.replace('_', ' ')}</span>
                          </div>
                          {exercise.attempts_count > 0 && (
                            <span className="attempts-badge">
                              {exercise.attempts_count} attempt{exercise.attempts_count > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="exercise-header-actions">
                          <button
                            onClick={() => handleEdit(exercise)}
                            className="btn-icon btn-edit-icon"
                            title="Edit exercise"
                          >
                            <Edit3 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(exercise.id, exercise.attempts_count)}
                            className="btn-icon btn-delete-icon"
                            disabled={exercise.attempts_count > 0}
                            title={exercise.attempts_count > 0 ? 'Cannot delete - students attempted' : 'Delete exercise'}
                          >
                            <Trash2 size={18} />
                          </button>
                          <button
                            onClick={() => toggleExpand(exercise.id)}
                            className="btn-icon btn-expand"
                            title={isExpanded ? 'Collapse' : 'Expand'}
                          >
                            {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                          </button>
                        </div>
                      </div>

                      {/* Exercise Preview */}
                      <div className="exercise-preview">
                        <p className="exercise-question">{exercise.question}</p>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="exercise-details">
                          {exercise.options && exercise.options.length > 0 && (
                            <div className="detail-section">
                              <strong>Options:</strong>
                              <ul className="options-list">
                                {exercise.options.map((option, idx) => (
                                  <li 
                                    key={idx}
                                    className={correctAnswerText === option ? 'correct-option' : ''}
                                  >
                                    {option}
                                    {correctAnswerText === option && <span className="check-mark"> ✓</span>}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {exercise.explanation && (
                            <div className="detail-section">
                              <strong>Explanation:</strong>
                              <p className="explanation-text">{exercise.explanation}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Exercise Editor Form */}
        {showEditor && editingExercise && (
          <div className="editor-form-container">
            <div className="editor-form-header">
              <h3>{isNewExercise ? '➕ Add New Exercise' : '✏️ Edit Exercise'}</h3>
            </div>

            <div className="editor-form">
              {/* Question */}
              <div className="form-group">
                <label className="form-label">Question *</label>
                <textarea
                  value={editingExercise.question}
                  onChange={(e) => setEditingExercise({
                    ...editingExercise,
                    question: e.target.value
                  })}
                  rows={3}
                  className="form-textarea"
                  placeholder="Enter the question..."
                  required
                />
              </div>

              {/* Type */}
              <div className="form-group">
                <label className="form-label">Type *</label>
                <select
                  value={editingExercise.type}
                  onChange={(e) => setEditingExercise({
                    ...editingExercise,
                    type: e.target.value
                  })}
                  className="form-select"
                >
                  <option value="multiple_choice">Multiple Choice</option>
                  <option value="fill_in_blank">Fill in the Blank</option>
                  <option value="true_false">True/False</option>
                  <option value="matching">Matching</option>
                  <option value="error_correction">Error Correction</option>
                </select>
              </div>

              {/* Options */}
              {editingExercise.type === 'multiple_choice' && (
                <div className="form-group">
                  <label className="form-label">Options *</label>
                  <div className="options-inputs">
                    {editingExercise.options.map((option, index) => (
                      <input
                        key={index}
                        type="text"
                        value={option}
                        onChange={(e) => {
                          const newOptions = [...editingExercise.options];
                          newOptions[index] = e.target.value;
                          setEditingExercise({
                            ...editingExercise,
                            options: newOptions
                          });
                        }}
                        className="form-input"
                        placeholder={`Option ${index + 1}`}
                      />
                    ))}
                  </div>
                  <button
                    onClick={() => setEditingExercise({
                      ...editingExercise,
                      options: [...editingExercise.options, '']
                    })}
                    className="btn-add-option"
                    type="button"
                  >
                    <Plus size={16} />
                    Add Option
                  </button>
                </div>
              )}

              {/* Correct Answer */}
              <div className="form-group">
                <label className="form-label">Correct Answer *</label>
                {renderCorrectAnswerSelector()}
              </div>

              {/* Explanation */}
              <div className="form-group">
                <label className="form-label">Explanation</label>
                <textarea
                  value={editingExercise.explanation}
                  onChange={(e) => setEditingExercise({
                    ...editingExercise,
                    explanation: e.target.value
                  })}
                  rows={2}
                  className="form-textarea"
                  placeholder="Optional explanation..."
                />
              </div>

              {/* Action Buttons */}
              <div className="form-actions">
                <button onClick={handleSave} className="btn-primary">
                  <Save size={18} />
                  {isNewExercise ? 'Add Exercise' : 'Save Changes'}
                </button>
                <button 
                  onClick={() => {
                    setShowEditor(false);
                    setEditingExercise(null);
                  }} 
                  className="btn-secondary"
                  type="button"
                >
                  <X size={18} />
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}