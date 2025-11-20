import React, { useState, useEffect } from 'react';
import { Trophy, Medal, Award, TrendingUp, Users, Target, Crown, Star } from 'lucide-react';
import { trainingAPI } from '../../services/api';
import '../../styles/Leaderboard.css';

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [currentUserRank, setCurrentUserRank] = useState(null);
  const [totalStudents, setTotalStudents] = useState(0);
  const [timePeriod, setTimePeriod] = useState('all_time');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, [timePeriod]);

  const loadLeaderboard = async () => {
    setLoading(true);
    try {
      const data = await trainingAPI.getLeaderboard(10, timePeriod);
      setLeaderboard(data.leaderboard || []);
      setCurrentUserRank(data.current_user_rank);
      setTotalStudents(data.total_students);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown size={24} className="rank-icon gold" />;
    if (rank === 2) return <Medal size={24} className="rank-icon silver" />;
    if (rank === 3) return <Award size={24} className="rank-icon bronze" />;
    return <span className="rank-number">#{rank}</span>;
  };

  const getRankClass = (rank) => {
    if (rank === 1) return 'rank-1';
    if (rank === 2) return 'rank-2';
    if (rank === 3) return 'rank-3';
    return '';
  };

  return (
    <div className="leaderboard-container">
      {/* Header */}
      <div className="leaderboard-header">
        <div className="header-title">
          <Trophy size={32} className="trophy-icon" />
          <h2>Leaderboard</h2>
        </div>
        
        {/* Time Period Filter */}
        <div className="time-filter">
          <button
            className={`filter-btn ${timePeriod === 'all_time' ? 'active' : ''}`}
            onClick={() => setTimePeriod('all_time')}
          >
            All Time
          </button>
          <button
            className={`filter-btn ${timePeriod === 'this_month' ? 'active' : ''}`}
            onClick={() => setTimePeriod('this_month')}
          >
            This Month
          </button>
          <button
            className={`filter-btn ${timePeriod === 'this_week' ? 'active' : ''}`}
            onClick={() => setTimePeriod('this_week')}
          >
            This Week
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="leaderboard-stats">
        <div className="stat-card">
          <Users size={24} />
          <div>
            <span className="stat-value">{totalStudents}</span>
            <span className="stat-label">Total Students</span>
          </div>
        </div>
        
        {currentUserRank && (
          <>
            <div className="stat-card highlight">
              <TrendingUp size={24} />
              <div>
                <span className="stat-value">#{currentUserRank.rank}</span>
                <span className="stat-label">Your Rank</span>
              </div>
            </div>
            <div className="stat-card">
              <Target size={24} />
              <div>
                <span className="stat-value">{currentUserRank.total_score}</span>
                <span className="stat-label">Your Score</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Leaderboard List */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading leaderboard...</p>
        </div>
      ) : (
        <div className="leaderboard-list">
          {leaderboard.map((student) => (
            <div
              key={student.student_id}
              className={`leaderboard-item ${getRankClass(student.rank)} ${
                student.is_current_user ? 'current-user' : ''
              }`}
            >
              {/* Rank */}
              <div className="item-rank">
                {getRankIcon(student.rank)}
              </div>

              {/* Student Info */}
              <div className="item-info">
                <div className="student-name">
                  {student.student_name}
                  {student.is_current_user && (
                    <span className="you-badge">You</span>
                  )}
                </div>
                <div className="student-username">@{student.username}</div>
                
                {/* Badges */}
                {student.badges.length > 0 && (
                  <div className="student-badges">
                    {student.badges.map((badge, idx) => (
                      <span key={idx} className="badge">
                        {badge}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Stats */}
              <div className="item-stats">
                <div className="stat">
                  <span className="stat-label">Score</span>
                  <span className="stat-value">{student.total_score}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Modules</span>
                  <span className="stat-value">{student.modules_completed}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Accuracy</span>
                  <span className="stat-value">{student.accuracy}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Your Position (if not in top 10) */}
      {currentUserRank && currentUserRank.rank > 10 && (
        <div className="your-position">
          <h3>Your Position</h3>
          <div className="leaderboard-item current-user">
            <div className="item-rank">
              <span className="rank-number">#{currentUserRank.rank}</span>
            </div>
            <div className="item-info">
              <div className="student-name">
                {currentUserRank.student_name}
                <span className="you-badge">You</span>
              </div>
              <div className="student-username">@{currentUserRank.username}</div>
            </div>
            <div className="item-stats">
              <div className="stat">
                <span className="stat-label">Score</span>
                <span className="stat-value">{currentUserRank.total_score}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Modules</span>
                <span className="stat-value">{currentUserRank.modules_completed}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Accuracy</span>
                <span className="stat-value">{currentUserRank.accuracy}%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}