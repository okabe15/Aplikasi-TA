// RegisterPage.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserPlus, User, Mail, Lock, BookOpen, GraduationCap } from 'lucide-react';
import '../styles/Auth.css';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    role: 'student'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    const result = await register({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      role: formData.role
    });

    if (result.success) {
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
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
          <p>Join Our Learning Community</p>
        </div>

        <div className="auth-form-container">
          <h2>
            <UserPlus size={24} />
            Create Your Account
          </h2>

          {error && (
            <div className="error-message">
              ❌ {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              ✅ Registration successful! Redirecting to login...
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
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Choose a username"
                required
                minLength={3}
              />
            </div>

            <div className="form-group">
              <label>
                <Mail size={18} />
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your.email@example.com"
                required
              />
            </div>

            <div className="form-group">
              <label>
                <User size={18} />
                Full Name
              </label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Your full name"
                required
              />
            </div>

            <div className="form-group">
              <label>
                <Lock size={18} />
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="At least 6 characters"
                required
                minLength={6}
              />
            </div>

            <div className="form-group">
              <label>
                <Lock size={18} />
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Re-enter your password"
                required
              />
            </div>

            <div className="form-group">
              <label>
                <GraduationCap size={18} />
                I am a...
              </label>
              <div className="role-selector">
                <label className={`role-option ${formData.role === 'student' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="role"
                    value="student"
                    checked={formData.role === 'student'}
                    onChange={handleChange}
                  />
                  <div className="role-content">
                    <span className="role-icon">👨‍🎓</span>
                    <div>
                      <strong>Student</strong>
                      <p>Learn and practice</p>
                    </div>
                  </div>
                </label>

                <label className={`role-option ${formData.role === 'teacher' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="role"
                    value="teacher"
                    checked={formData.role === 'teacher'}
                    onChange={handleChange}
                  />
                  <div className="role-content">
                    <span className="role-icon">👨‍🏫</span>
                    <div>
                      <strong>Teacher</strong>
                      <p>Create modules</p>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading || success}
            >
              {loading ? 'Creating Account...' : 'Register'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login">Login here</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}