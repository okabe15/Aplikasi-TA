import React, { useState, useEffect, useRef } from 'react';
import { GraduationCap, BookOpen, Trophy, ArrowLeft, Database, Volume2, VolumeX } from 'lucide-react';
import { trainingAPI, moduleAPI } from '../../services/api';

export default function TrainingMode({ 
  classicText, 
  modernText,
  comicScript,
  panels,
  onBack,
  preloadedExercises = null,
  selectedModule = null
}) {
  // ✅ TAMBAH: Detect user role
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isTeacher = user.role === 'teacher';

  const [topics, setTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [score, setScore] = useState({ total: 0, correct: 0, answered: 0 });
  const [trainingStarted, setTrainingStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [userAnswers, setUserAnswers] = useState([]);
  const [trainingCompleted, setTrainingCompleted] = useState(false);
  const [resultsSaved, setResultsSaved] = useState(false);
  const [savedModuleId, setSavedModuleId] = useState(null);
  const [moduleName, setModuleName] = useState(''); 
  
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    loadTopics();
  }, []);

  useEffect(() => {
  if (preloadedExercises && preloadedExercises.length > 0) {
    console.log(`✅ Student: Using ${preloadedExercises.length} pre-loaded exercises from DB`);
    setExercises(preloadedExercises);
    setTrainingStarted(true);
  }
}, [preloadedExercises]);


  useEffect(() => {
    return () => {
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };

    // ✅ ADD: Auto-generate default module name from classic text
    if (classicText && !moduleName && isTeacher) {
      const firstLine = classicText.split('\n')[0];
      const defaultName = firstLine.length > 60 
        ? firstLine.substring(0, 60) + '...' 
        : firstLine;
      setModuleName(defaultName || 'Untitled Module');
    }
  }, [classicText, moduleName, isTeacher]);

  const cleanTextForTTS = (text) => {
    if (!text) return '';
    
    let cleaned = text.trim();
    
    cleaned = cleaned.replace(/\*\*([^*]+):\*\*/g, '$1:');
    cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1');
    cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1');
    
    cleaned = cleaned.replace(/<[^>]*>/g, '');
    
    cleaned = cleaned.replace(/&quot;/g, '"');
    cleaned = cleaned.replace(/&apos;/g, "'");
    cleaned = cleaned.replace(/&lt;/g, '<');
    cleaned = cleaned.replace(/&gt;/g, '>');
    cleaned = cleaned.replace(/&amp;/g, '&');
    
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    
    if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
      cleaned = cleaned.slice(1, -1);
    }
    if (cleaned.startsWith("'") && cleaned.endsWith("'")) {
      cleaned = cleaned.slice(1, -1);
    }
    
    return cleaned;
  };

  const audioCacheRef = useRef({});

  const playExerciseAudio = async (text, voiceType = 'modern') => {
    if (!text) return;
    
    const cleanText = cleanTextForTTS(text);
    const cacheKey = `${cleanText}-${voiceType}`;
    
    if (audioRef.current && !audioRef.current.paused) {
      console.log('⏹️ Stopping audio');
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setAudioPlaying(false);
      return;
    }
    
    setAudioLoading(true);
    
    try {
      let audioUrl = audioCacheRef.current[cacheKey];
      
      if (!audioUrl) {
        console.log('🎵 Generating new audio...');
        
        audioUrl = await moduleAPI.generateAudio(
          cleanText,
          voiceType,
          'medium',
          'medium',
          false
        );
        
        if (audioUrl) {
          audioCacheRef.current[cacheKey] = audioUrl;
          console.log('💾 Audio cached');
        }
      } else {
        console.log('✅ Using cached audio (no regenerate)');
      }
      
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        
        audio.onplay = () => {
          setAudioLoading(false);
          setAudioPlaying(true);
          console.log('▶️ Audio playing');
        };
        
        audio.onended = () => {
          setAudioPlaying(false);
          console.log('⏹️ Audio ended (can replay)');
        };
        
        audio.onerror = (e) => {
          console.error('❌ Audio error:', e);
          setAudioLoading(false);
          setAudioPlaying(false);
          audioRef.current = null;
          alert('Audio playback failed');
        };
        
        await audio.play();
      }
    } catch (error) {
      console.error('❌ Failed to generate audio:', error);
      setAudioLoading(false);
      setAudioPlaying(false);
      alert('Failed to generate audio: ' + error.message);
    }
  };

  useEffect(() => {
    return () => {
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      Object.values(audioCacheRef.current).forEach(url => {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      });
      audioCacheRef.current = {};
    };
  }, []);

  const loadTopics = async () => {
    try {
      const data = await trainingAPI.getTopics();
      console.log('📚 Topics received:', data);
      
      const topicsArray = data.topics || [];
      setTopics(topicsArray);
      
      const basicTopics = topicsArray.filter(t => t.is_basic).map(t => t.id);
      setSelectedTopics(basicTopics);
    } catch (error) {
      console.error('Failed to load topics:', error);
      setTopics([]);
      setSelectedTopics([]);
    }
  };

  const handleTopicToggle = (topicId) => {
    setSelectedTopics(prev => 
      prev.includes(topicId) 
        ? prev.filter(id => id !== topicId)
        : [...prev, topicId]
    );
  };

  // ✅ UBAH: Teacher langsung save, Student mulai training
  const handleStartTraining = async () => {
    if (selectedTopics.length === 0) {
      alert('Please select at least one topic');
      return;
    }

    setLoading(true);
    try {
      const response = await trainingAPI.generateExercises({
        classic_text: classicText,
        modern_text: modernText,
        panels: panels,
        selected_topics: selectedTopics,
        num_questions: 6
      });

      setExercises(response.exercises);
      
      // ✅ TEACHER: Save immediately, no training
      // ✅ TEACHER: Save immediately, no training
      if (isTeacher) {
        console.log('💾 Teacher mode: Saving module + exercises...');
        
        // ✅ Validate module name
        if (!moduleName.trim()) {
          alert('Please enter a module name');
          setLoading(false);
          return;
        }
        
        const base64Images = window.savedBase64Images || [];
        const panelAudios = window.savedPanelAudios || [];
        
        const scriptString = typeof comicScript === 'string' 
          ? comicScript 
          : comicScript?.raw_script || JSON.stringify(comicScript);
        
        // ✅ ADD: Ensure all panels have required fields
        const panelsWithSettings = panels.map(panel => ({
          ...panel,
          setting: panel.setting || '',
          mood: panel.mood || '',
          composition: panel.composition || ''
        }));
        
        const result = await trainingAPI.saveModuleWithExercises(
          moduleName.trim(),  // ✅ ADD module name as FIRST param
          classicText,
          modernText,
          scriptString,
          panelsWithSettings,  // ✅ Use enhanced panels
          response.exercises,
          base64Images,
          panelAudios
        );

        setResultsSaved(true);
        setSavedModuleId(result.module_id);
        setTrainingCompleted(true);
        
      } else {
        // ✅ STUDENT: Start training normally
        setTrainingStarted(true);
        setCurrentExerciseIndex(0);
        setScore({ total: 0, correct: 0, answered: 0 });
        setUserAnswers([]);
        setTrainingCompleted(false);
        setResultsSaved(false);
      }
      
    } catch (error) {
      alert(`Failed to generate exercises: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (answerIndex) => {
    if (showFeedback) return;
    setSelectedAnswer(answerIndex);
  };

  const handleSubmitAnswer = () => {
    if (selectedAnswer === null) {
      alert('Please select an answer');
      return;
    }

    const currentExercise = exercises[currentExerciseIndex];
    const isCorrect = selectedAnswer === currentExercise.correct;

    setScore(prev => ({
      total: prev.total + (isCorrect ? 10 : 0),
      correct: prev.correct + (isCorrect ? 1 : 0),
      answered: prev.answered + 1
    }));

    setUserAnswers(prev => [...prev, {
      exercise_id: currentExercise.id,
      selected_answer: selectedAnswer,
      is_correct: isCorrect
    }]);

    setShowFeedback(true);
  };

  const handleNextExercise = () => {
    if (currentExerciseIndex < exercises.length - 1) {
      setCurrentExerciseIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowFeedback(false);
    } else {
      setTrainingCompleted(true);
    }
  };

 const handleSaveAllResults = async () => {
  if (exercises.length === 0) {
    alert('No exercises to save');
    return;
  }

  setLoading(true);
  try {
    // ✅ Get module ID from preloaded exercises (if student used existing module)
    const moduleId = exercises[0]?.module_id || selectedModule?.id;
    
    if (!moduleId) {
      alert('Module ID not found. Cannot save progress.');
      return;
    }

    console.log('💾 Saving student answers...', {
      moduleId,
      answers: userAnswers.length,
      score: score.total
    });
    
    // ✅ Save only student answers (not module/exercises)
    const result = await trainingAPI.saveStudentAnswers(
      moduleId,
      userAnswers,
      score.total
    );

    setResultsSaved(true);
    setSavedModuleId(result.module_id);
    
    alert(`✅ Successfully saved your progress!\n\n` +
          `📦 Module ID: ${result.module_id}\n` +
          `✏️ ${result.answers_saved} answers saved\n` +
          `🎯 Final Score: ${score.total} points\n` +
          `✅ Correct: ${score.correct}/${exercises.length}`);
  } catch (error) {
    console.error('Save error:', error);
    alert(`Failed to save progress: ${error.message}`);
  } finally {
    setLoading(false);
  }
};

  const handleRestartTraining = () => {
    setTrainingStarted(false);
    setCurrentExerciseIndex(0);
    setSelectedAnswer(null);
    setShowFeedback(false);
    setScore({ total: 0, correct: 0, answered: 0 });
    setExercises([]);
    setUserAnswers([]);
    setTrainingCompleted(false);
    setResultsSaved(false);
    setSavedModuleId(null);
  };

  // Topic Selection Screen
  if (!trainingStarted && !preloadedExercises) {
    return (
      <div className="training-mode"> 
        <div className="section-header">
          <GraduationCap size={24} />
          <h2>Training Mode - Grammar & Vocabulary Exercises</h2>
        </div>

        <button onClick={onBack} className="btn btn-secondary">
          <ArrowLeft size={16} /> Back to Comic
        </button>

          {/* ✅ ADD: Module Name Input (TEACHER ONLY) */}
        {isTeacher && (
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '20px',
            marginTop: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <label style={{
              display: 'block',
              fontSize: '16px',
              fontWeight: '600',
              marginBottom: '10px',
              color: '#333'
            }}>
              📝 Module Name: <span style={{color: '#dc3545'}}>*</span>
            </label>
            <input
              type="text"
              value={moduleName}
              onChange={(e) => setModuleName(e.target.value)}
              placeholder="Enter a descriptive name for this module..."
              maxLength={100}
              style={{
                width: '100%',
                padding: '12px 16px',
                fontSize: '16px',
                border: '2px solid #e0e0e0',
                borderRadius: '8px',
                outline: 'none',
                transition: 'border-color 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
            />
            <small style={{color: '#666', fontSize: '14px', marginTop: '5px', display: 'block'}}>
              💡 This name will help students identify the module easily
            </small>
          </div>
        )}

        <div className="info-box">
          <h3>📚 How It Works</h3>
          <div className="features-grid">
            <div className="feature">
              <strong>1. Choose Topics</strong>
              <p>Select grammar topics you want to practice</p>
            </div>
            <div className="feature">
              <strong>2. {isTeacher ? 'Generate & Save' : 'Answer Questions'}</strong>
              <p>{isTeacher ? 'Exercises will be saved for students' : 'Complete all exercises with instant feedback'}</p>
            </div>
            <div className="feature">
              <strong>3. {isTeacher ? 'Students Train' : 'Save Progress'}</strong>
              <p>{isTeacher ? 'Students can start training' : 'Your answers saved to database'}</p>
            </div>
          </div>
        </div>

        <div className="topic-selector">
          <h4>Select Grammar Topics to Practice:</h4>
          <div className="topic-grid">
            {topics.map(topic => (
              <div key={topic.id} className="topic-item" onClick={() => handleTopicToggle(topic.id)}>
                <input
                  type="checkbox"
                  checked={selectedTopics.includes(topic.id)}
                  onChange={() => {}}
                />
                <div className="topic-info">
                  <strong>{topic.label}</strong>
                  {topic.is_basic && <span className="badge">BASIC</span>}
                  <div className="topic-desc">{topic.description}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="topic-selection-summary">
            <p>
              Selected: <strong>{selectedTopics.length}</strong> topic(s)
              {selectedTopics.length === 0 && (
                <span className="text-warning"> - Please select at least one topic</span>
              )}
            </p>
          </div>

          <button
            onClick={handleStartTraining}
            className="btn btn-primary"
            disabled={selectedTopics.length === 0 || loading}
          >
            {loading ? 'Generating Exercises...' : isTeacher ? '💾 Generate & Save Module' : '🚀 Generate Exercises & Start Training'}
          </button>
        </div>
      </div>
    );
  }

  // ✅ UBAH: Training Complete Screen - Different untuk Teacher vs Student
  if (trainingCompleted) {
    return (
      <div className="training-mode">
        <div className="training-complete">
          <div className="completion-card">
            {isTeacher ? (
              // ✅ TEACHER: Show save success
              <>
                <Database size={64} color="#28a745" />
                <h2>✅ Module Saved Successfully!</h2>
                
                <div className="save-success-banner">
                  ✅ Module & exercises saved to database!
                  <br />
                  <strong>Module ID:</strong> <code>{savedModuleId}</code>
                  <br />
                  <strong>Exercises:</strong> {exercises.length} questions created
                  <br />
                  <strong>Panels:</strong> {panels.length} comic panels
                  <br />
                  <small>Students can now start training on this module</small>
                </div>

                <div className="info-box" style={{background: '#e7f3ff', border: '2px solid #667eea', marginTop: '20px'}}>
                  <h4>📚 What's Next?</h4>
                  <ul style={{textAlign: 'left', marginLeft: '20px'}}>
                    <li>Students can now see this module in their dashboard</li>
                    <li>They can start training and answering exercises</li>
                    <li>You can track their progress in "Student Progress" tab</li>
                  </ul>
                </div>

                <div className="button-group" style={{marginTop: '30px'}}>
                  <button onClick={onBack} className="btn btn-primary">
                    ← Back to Dashboard
                  </button>
                </div>
              </>
            ) : (
              // ✅ STUDENT: Show score and save option
              <>
                <Trophy size={64} color="#28a745" />
                <h2>🎉 Training Complete!</h2>
                
                <div className="final-score">
                  <h3>Your Results:</h3>
                  <p>Total Score: <strong>{score.total} points</strong></p>
                  <p>Correct Answers: <strong>{score.correct} / {exercises.length}</strong></p>
                  <p>Accuracy: <strong>{((score.correct / exercises.length) * 100).toFixed(0)}%</strong></p>
                </div>

                {!resultsSaved ? (
                  <div className="save-section">
                    <div className="info-box" style={{background: '#e7f3ff', border: '2px solid #667eea'}}>
                      <h3><Database size={24} /> Save Everything to Database</h3>
                      <p>Click the button below to save all your work:</p>
                      <ul>
                        <li><strong>Comic Module:</strong> {panels.length} panels with images & audio</li>
                        <li><strong>Training Exercises:</strong> {exercises.length} questions & explanations</li>
                        <li><strong>Your Answers:</strong> {userAnswers.length} responses with results</li>
                        <li><strong>Your Score:</strong> {score.total} points ({score.correct}/{exercises.length} correct)</li>
                      </ul>
                    </div>

                    <button 
                      onClick={handleSaveAllResults}
                      className="btn btn-success"
                      disabled={loading}
                      style={{fontSize: '20px', padding: '18px 40px', marginTop: '20px'}}
                    >
                      {loading ? 'Saving to Database...' : '💾 Save Everything to Database'}
                    </button>
                  </div>
                ) : (
                  <div className="save-success-banner">
                    ✅ All data successfully saved to database!
                    <br />
                    <strong>Module ID:</strong> <code>{savedModuleId}</code>
                    <br />
                    <small>Comic, Exercises, and Your Progress are now stored permanently</small>
                  </div>
                )}

                <div className="button-group" style={{marginTop: '30px'}}>
                  <button onClick={handleRestartTraining} className="btn btn-primary">
                    🔄 Practice Again (New Session)
                  </button>
                  <button onClick={onBack} className="btn btn-secondary">
                    <ArrowLeft size={16} /> Back to Comic
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }
  
  if (!exercises || exercises.length === 0) {
    return (
      <div className="training-mode">
        <div style={{padding: '40px', textAlign: 'center'}}>
          <h3>⏳ Loading exercises...</h3>
        </div>
      </div>
    );
  }

  // Exercise Screen (STUDENT ONLY - Teacher never sees this)
  const currentExercise = exercises[currentExerciseIndex];

  // ✅ ADD THIS TOO:
  if (!currentExercise) {
    return (
      <div className="training-mode">
        <div style={{padding: '40px', textAlign: 'center', color: '#dc3545'}}>
          <h3>❌ Exercise not found</h3>
          <button onClick={onBack} className="btn btn-secondary">
            ← Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="training-mode">
      <div className="section-header">
        <GraduationCap size={24} />
        <h2>Training Exercise</h2>
      </div>

      <button onClick={onBack} className="btn btn-secondary">
        <ArrowLeft size={16} /> Back to Comic
      </button>

      <div className="score-display">
        <div className="score-header">
          <Trophy size={24} />
          <h3>Your Progress</h3>
        </div>
        <div className="score-stats">
          <div className="score-stat">
            <div className="score-number">{score.total}</div>
            <div className="score-label">Points</div>
          </div>
          <div className="score-stat">
            <div className="score-number">{score.correct}/{score.answered}</div>
            <div className="score-label">Correct</div>
          </div>
          <div className="score-stat">
            <div className="score-number">
              {score.answered > 0 ? Math.round((score.correct / score.answered) * 100) : 0}%
            </div>
            <div className="score-label">Accuracy</div>
          </div>
        </div>
      </div>

      <div className="progress-indicator">
        Question {currentExerciseIndex + 1} of {exercises.length}
      </div>

      <div className="exercise-card">
        <div className="exercise-header">
          <span 
            className="exercise-type"
            style={{
              background: currentExercise.type === 'pronunciation' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#667eea'
            }}
          >
            {currentExercise.type === 'pronunciation' ? '🎧 PRONUNCIATION' : currentExercise.type.toUpperCase()}
          </span>
          <span className="exercise-score">10 points</span>
        </div>

        <div className="exercise-question">
          <h3>{currentExercise.question}</h3>

          {currentExercise.audio_text && currentExercise.audio_type && (
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '12px',
              padding: '20px',
              margin: '20px 0',
              color: 'white'
            }}>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                🎧 Listen to the audio:
                {currentExercise.audio_type && (
                  <span style={{
                    background: 'rgba(255, 255, 255, 0.2)',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontSize: '14px',
                    marginLeft: '10px'
                  }}>
                    {currentExercise.audio_type === 'classic' ? '📜 Classic' : 
                     currentExercise.audio_type === 'modern' ? '🔊 Modern' : '🔄 Both'}
                  </span>
                )}
              </div>
              
              <button 
                onClick={() => playExerciseAudio(
                  currentExercise.audio_text, 
                  currentExercise.audio_type || 'modern'
                )}
                disabled={audioLoading}
                style={{
                  background: audioPlaying ? '#dc3545' : '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '25px',
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: audioLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.3s ease',
                  opacity: audioLoading ? 0.7 : 1
                }}
              >
                {audioLoading ? (
                  <>⏳ Loading Audio...</>
                ) : audioPlaying ? (
                  <>
                    <VolumeX size={20} />
                    Stop Audio
                  </>
                ) : (
                  <>
                    <Volume2 size={20} />
                    🔊 Play Audio
                  </>
                )}
              </button>
            </div>
          )}

          {currentExercise.classic_text && (
            <div className="classic-text-sample">
              <strong>Classic:</strong> {currentExercise.classic_text}
            </div>
          )}

          {currentExercise.modern_text && (
            <div className="modern-text-sample">
              <strong>Modern:</strong> {currentExercise.modern_text}
            </div>
          )}

          {currentExercise.comic_reference && (
            <div className="comic-reference">
              <BookOpen size={16} /> Reference: {currentExercise.comic_reference}
            </div>
          )}
        </div>

        <div className="answer-options">
          {currentExercise.options.map((option, index) => (
            <div
              key={index}
              className={`answer-option ${
                selectedAnswer === index ? 'selected' : ''
              } ${
                showFeedback && index === currentExercise.correct ? 'correct' : ''
              } ${
                showFeedback && selectedAnswer === index && index !== currentExercise.correct ? 'incorrect' : ''
              }`}
              onClick={() => handleAnswerSelect(index)}
            >
              <span className="option-letter">{String.fromCharCode(65 + index)}</span>
              <span className="option-text">{option}</span>
            </div>
          ))}
        </div>

        {showFeedback && (
          <>
            <div className={`answer-feedback ${selectedAnswer === currentExercise.correct ? 'correct' : 'incorrect'}`}>
              {selectedAnswer === currentExercise.correct ? '✅ Correct! +10 points' : '❌ Incorrect'}
            </div>

            <div className="explanation-box">
              <h5>💡 Explanation:</h5>
              <p>{currentExercise.explanation}</p>
              {currentExercise.grammar_rule && (
                <div className="grammar-rule">
                  <strong>Grammar Rule:</strong> {currentExercise.grammar_rule}
                </div>
              )}
            </div>
          </>
        )}

        <div className="button-group">
          {!showFeedback ? (
            <button 
              onClick={handleSubmitAnswer} 
              className="btn btn-primary"
              disabled={selectedAnswer === null}
            >
              Submit Answer
            </button>
          ) : (
            <button onClick={handleNextExercise} className="btn btn-success">
              {currentExerciseIndex < exercises.length - 1 ? 'Next Question →' : 'Complete Training →'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}