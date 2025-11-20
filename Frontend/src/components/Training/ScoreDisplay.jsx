import React from 'react';
import { Trophy } from 'lucide-react';

export default function ScoreDisplay({ score, totalQuestions }) {
  const accuracy = score.answered > 0 
    ? Math.round((score.correct / score.answered) * 100) 
    : 0;

  return (
    <div className="score-display">
      <div className="score-header">
        <Trophy size={24} />
        <h3>Your Progress</h3>
      </div>
      
      <div className="score-stats">
        <div className="score-stat">
          <div className="score-number">{score.total}</div>
          <div className="score-label">Total Score</div>
        </div>
        <div className="score-stat">
          <div className="score-number">{score.correct}/{totalQuestions}</div>
          <div className="score-label">Correct Answers</div>
        </div>
        <div className="score-stat">
          <div className="score-number">{accuracy}%</div>
          <div className="score-label">Accuracy</div>
        </div>
      </div>
    </div>
  );
}