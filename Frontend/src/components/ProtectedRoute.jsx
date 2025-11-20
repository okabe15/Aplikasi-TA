// ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ children, requireTeacher = false }) {
  const { user, loading, isAuthenticated, isTeacher } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireTeacher && !isTeacher()) {
    return (
      <div className="access-denied">
        <h2>🚫 Access Denied</h2>
        <p>Only teachers can access this page.</p>
        <a href="/dashboard" className="btn btn-primary">Go to Dashboard</a>
      </div>
    );
  }

  return children;
}