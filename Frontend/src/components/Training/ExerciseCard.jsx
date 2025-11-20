import React, { useState } from 'react';
import { Volume2, CheckCircle, XCircle } from 'lucide-react';
import { moduleAPI } from '../../services/api';

export default function ExerciseCard({ 
  exercise, 
  onAnswerSubmit, 
  onNext, 
  isLastExercise 
}) {
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleAnswerSelect = (index) => {
    if (isAnswered) return;
    setSelectedAnswer(index);
  };

  const handleCheckAnswer = () => {
    if (selectedAnswer === null) return;

    setIsAnswered(true);
    setShowExplanation(true);
    const isCorrect = selectedAnswer === exercise.correct;
    onAnswerSubmit(isCorrect);

    // Play audio feedback if pronunciation question
    if (exercise.audio_text && exercise.audio_type) {
      setTimeout(() => {
        playAudio(exercise.audio_text, exercise.audio_type);
      }, 1000);
    }
  };

  const handleNext = () => {
    setSelectedAnswer(null);
    setIsAnswered(false);
    setShowExplanation(false);
    onNext();
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

  const isCorrect = isAnswered && selectedAnswer === exercise.correct;

  return (
    <div className="exercise-card">
      <div className="exercise-header">
        <span className="exercise-type">{exercise.type.toUpperCase()}</span>
      </div>

      <div className="exercise-question">
        <h3>{exercise.question}</h3>
      </div>

      {exercise.classic_text && (
        <div className="classic-text-sample">
          <strong>Original Classic Text:</strong> "{exercise.classic_text}"
        </div>
      )}

      {exercise.modern_text && (
        <div className="modern-text-sample">
          <strong>Modern Version:</strong> "{exercise.modern_text}"
        </div>
      )}

      {exercise.comic_reference && (
        <div className="comic-reference">
          <strong>Comic Reference:</strong> {exercise.comic_reference}
        </div>
      )}

      {exercise.audio_text && exercise.audio_type && (
        <div className="audio-controls">
          {exercise.audio_type === 'both' ? (
            <>
              <button
                onClick={() => playAudio(exercise.audio_text, 'classic')}
                className="btn btn-audio"
              >
                <Volume2 size={16} />
                Play Classic Pronunciation
              </button>
              <button
                onClick={() => playAudio(exercise.audio_text, 'modern')}
                className="btn btn-audio"
              >
                <Volume2 size={16} />
                Play Modern Pronunciation
              </button>
            </>
          ) : (
            <button
              onClick={() => playAudio(exercise.audio_text, exercise.audio_type)}
              className="btn btn-audio"
            >
              <Volume2 size={16} />
              Play {exercise.audio_type === 'classic' ? 'Classic' : 'Modern'} Pronunciation
            </button>
          )}
        </div>
      )}

      <div className="answer-options">
        {exercise.options.map((option, index) => (
          <div
            key={index}
            className={`answer-option ${
              selectedAnswer === index ? 'selected' : ''
            } ${
              isAnswered && index === exercise.correct ? 'correct' : ''
            } ${
              isAnswered && selectedAnswer === index && index !== exercise.correct ? 'incorrect' : ''
            }`}
            onClick={() => handleAnswerSelect(index)}
          >
            <span className="option-letter">{String.fromCharCode(65 + index)}.</span>
            <span className="option-text">{option}</span>
            {isAnswered && index === exercise.correct && (
              <CheckCircle size={20} color="#28a745" />
            )}
            {isAnswered && selectedAnswer === index && index !== exercise.correct && (
              <XCircle size={20} color="#dc3545" />
            )}
          </div>
        ))}
      </div>

      {isAnswered && (
        <div className={`answer-feedback ${isCorrect ? 'correct' : 'incorrect'}`}>
          {isCorrect ? (
            <p>✅ Excellent! You understood the transformation correctly!</p>
          ) : (
            <p>
              ❌ Not quite right. The correct answer was: {String.fromCharCode(65 + exercise.correct)}.{' '}
              {exercise.options[exercise.correct]}
            </p>
          )}
        </div>
      )}

      {showExplanation && (
        <div className="explanation-box">
          <h5>Educational Explanation:</h5>
          <p>{exercise.explanation}</p>
          {exercise.grammar_rule && (
            <div className="grammar-rule">
              <strong>Grammar Rule:</strong> {exercise.grammar_rule}
            </div>
          )}
        </div>
      )}

      <div className="exercise-controls">
        {!isAnswered ? (
          <button
            onClick={handleCheckAnswer}
            className="btn btn-primary"
            disabled={selectedAnswer === null}
          >
            Check Answer
          </button>
        ) : (
          <button onClick={handleNext} className="btn btn-success">
            {isLastExercise ? 'Complete Training' : 'Next Question →'}
          </button>
        )}
      </div>
    </div>
  );
}