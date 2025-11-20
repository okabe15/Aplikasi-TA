import React from 'react';
import { X, TrendingUp, Users, Award, BarChart } from 'lucide-react';
import { 
  BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  PieChart, Pie, Cell, LineChart, Line, ResponsiveContainer
} from 'recharts';

export default function ReportPreview({ reportType, data, onClose }) {
  const COLORS = ['#667eea', '#48bb78', '#ed8936', '#f56565', '#38b2ac'];

  const renderPreviewContent = () => {
    switch (reportType.id) {
      case 'student_progress':
        return renderStudentProgressPreview();
      case 'class_overview':
        return renderClassOverviewPreview();
      case 'module_performance':
        return renderModulePerformancePreview();
      case 'exercise_analysis':
        return renderExerciseAnalysisPreview();
      default:
        return renderDefaultPreview();
    }
  };

  const renderStudentProgressPreview = () => (
    <div className="preview-content">
      <div className="preview-stats">
        <div className="stat-card">
          <TrendingUp size={24} className="stat-icon" />
          <div>
            <h4>Average Score</h4>
            <p className="stat-value">85.5%</p>
          </div>
        </div>
        <div className="stat-card">
          <Award size={24} className="stat-icon" />
          <div>
            <h4>Modules Completed</h4>
            <p className="stat-value">8/12</p>
          </div>
        </div>
        <div className="stat-card">
          <BarChart size={24} className="stat-icon" />
          <div>
            <h4>Total Points</h4>
            <p className="stat-value">1,250</p>
          </div>
        </div>
      </div>

      <div className="preview-chart">
        <h4>Weekly Progress</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={[
            { week: 'Week 1', score: 75 },
            { week: 'Week 2', score: 80 },
            { week: 'Week 3', score: 78 },
            { week: 'Week 4', score: 85 },
            { week: 'Week 5', score: 88 },
            { week: 'Week 6', score: 92 }
          ]}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#667eea" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderClassOverviewPreview = () => (
    <div className="preview-content">
      <div className="preview-stats">
        <div className="stat-card">
          <Users size={24} className="stat-icon" />
          <div>
            <h4>Total Students</h4>
            <p className="stat-value">{data.sample_data.total_students}</p>
          </div>
        </div>
        <div className="stat-card">
          <TrendingUp size={24} className="stat-icon" />
          <div>
            <h4>Average Score</h4>
            <p className="stat-value">{data.sample_data.average_score}%</p>
          </div>
        </div>
        <div className="stat-card">
          <Award size={24} className="stat-icon" />
          <div>
            <h4>Completion Rate</h4>
            <p className="stat-value">{data.sample_data.completion_rate}%</p>
          </div>
        </div>
      </div>

      <div className="preview-chart">
        <h4>Top Performers</h4>
        <ResponsiveContainer width="100%" height={200}>
          <RechartsBarChart data={data.sample_data.top_performers}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="score" fill="#667eea" />
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderModulePerformancePreview = () => (
    <div className="preview-content">
      <div className="preview-stats">
        <div className="stat-card full-width">
          <h4>Module Performance Overview</h4>
          <p>Analysis of student performance across different learning modules</p>
        </div>
      </div>

      <div className="preview-chart">
        <h4>Success Rate by Module</h4>
        <ResponsiveContainer width="100%" height={250}>
          <RechartsBarChart data={[
            { module: 'Module 1', rate: 85 },
            { module: 'Module 2', rate: 78 },
            { module: 'Module 3', rate: 92 },
            { module: 'Module 4', rate: 70 },
            { module: 'Module 5', rate: 88 }
          ]}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="module" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="rate" fill="#48bb78" />
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderExerciseAnalysisPreview = () => (
    <div className="preview-content">
      <div className="preview-stats">
        <div className="stat-card full-width">
          <h4>Exercise Type Analysis</h4>
          <p>Performance breakdown by different exercise types</p>
        </div>
      </div>

      <div className="preview-chart">
        <h4>Success Rate by Exercise Type</h4>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={[
                { name: 'Multiple Choice', value: 85 },
                { name: 'Fill in Blank', value: 72 },
                { name: 'True/False', value: 90 },
                { name: 'Matching', value: 68 },
                { name: 'Error Correction', value: 65 }
              ]}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {COLORS.map((color, index) => (
                <Cell key={`cell-${index}`} fill={color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderDefaultPreview = () => (
    <div className="preview-content">
      <div className="preview-message">
        <p>Preview for this report type is being generated...</p>
        <p>The full report will include:</p>
        <ul>
          <li>Detailed statistics and metrics</li>
          <li>Visual charts and graphs</li>
          <li>Comprehensive data analysis</li>
          <li>Actionable insights</li>
        </ul>
      </div>
    </div>
  );

  return (
    <div className="report-preview-modal">
      <div className="preview-container">
        <div className="preview-header">
          <h3>{reportType.name} - Preview</h3>
          <button onClick={onClose} className="btn-close">
            <X size={24} />
          </button>
        </div>

        {renderPreviewContent()}

        <div className="preview-footer">
          <p>This is a preview showing sample data. Generate the full report to see actual data.</p>
        </div>
      </div>
    </div>
  );
}