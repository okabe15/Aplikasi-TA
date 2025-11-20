// LoginPage.jsx - FIXED: Role-based redirect
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, User, Lock, BookOpen } from 'lucide-react';
import '../styles/Auth.css';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login, user } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);

    if (result.success) {
      // ✅ FIXED: Redirect based on user role
      // Wait a bit for user data to be loaded
      setTimeout(() => {
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        
        if (userData.role === 'teacher') {
          navigate('/teacher-dashboard');
        } else if (userData.role === 'student') {
          navigate('/student-dashboard');
        } else {
          navigate('/dashboard'); // fallback
        }
      }, 100);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <BookOpen size={48} color="#667eea" />
          <h1>E-Learning Comics</h1>
          <p>Transform Classic English into Interactive Learning</p>
        </div>

        <div className="auth-form-container">
          <h2>
            <LogIn size={24} />
            Login to Your Account
          </h2>

          {error && (
            <div className="error-message">
              ❌ {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>
                <User size={18} />
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label>
                <Lock size={18} />
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register">Register here</Link>
            </p>
          </div>
        </div>

        <div className="role-info">
          <div className="role-card">
            <h4>👨‍🏫 Teacher Account</h4>
            <p>Create and manage learning modules</p>
          </div>
          <div className="role-card">
            <h4>👨‍🎓 Student Account</h4>
            <p>Learn and practice with interactive exercises</p>
          </div>
        </div>
      </div>
    </div>
  );
}