// App.jsx - FIXED VERSION with proper routing
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDashboard from './components/StudentDashboard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Teacher Routes */}
          <Route 
            path="/teacher-dashboard" 
            element={
              <ProtectedRoute requireTeacher={true}>
                <TeacherDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Student Routes */}
          <Route 
            path="/student-dashboard" 
            element={
              <ProtectedRoute>
                <StudentDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Fallback Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <RoleBasedRedirect />
              </ProtectedRoute>
            } 
          />

          {/* Default Route */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

// Component to redirect based on role
function RoleBasedRedirect() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  
  if (user.role === 'teacher') {
    return <Navigate to="/teacher-dashboard" replace />;
  } else if (user.role === 'student') {
    return <Navigate to="/student-dashboard" replace />;
  }
  
  return <Navigate to="/login" replace />;
}

export default App;