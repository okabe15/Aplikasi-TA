import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Calendar, Filter, Users, BookOpen, 
  TrendingUp, Award, Clock, Eye, Loader, BarChart3,
  PieChart, FileSpreadsheet, FileJson, AlertCircle
} from 'lucide-react';
import { reportAPI, userAPI, moduleAPI } from '../../services/api';
import ReportPreview from './Reportpreview';
import ReportFilters from './Reportfilters';
import '../../styles/Reports.css';

export default function Reports() {
  const [reportTypes, setReportTypes] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    student_id: null,
    module_id: null,
    date_from: null,
    date_to: null,
    format: 'pdf',
    comparison_type: 'students'  // ✅ ADD THIS
  });
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [students, setStudents] = useState([]);
  const [modules, setModules] = useState([]);
  const [scheduledReports, setScheduledReports] = useState([]);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadReportTypes();
    loadStudents();
    loadModules();
    loadScheduledReports();
  }, []);

  const loadReportTypes = async () => {
    try {
      const data = await reportAPI.getReportTypes();
      setReportTypes(data.report_types || []);
    } catch (error) {
      console.error('Failed to load report types:', error);
      setError('Failed to load report types. Please check backend connection.');
    }
  };

  const loadStudents = async () => {
    try {
      const data = await userAPI.listUsers({ role_filter: 'student', limit: 100 });
      setStudents(data.users || []);
    } catch (error) {
      console.error('Failed to load students:', error);
    }
  };

  const loadModules = async () => {
    try {
      const data = await moduleAPI.listModules(100);
      setModules(data.modules || []);
    } catch (error) {
      console.error('Failed to load modules:', error);
    }
  };

  const loadScheduledReports = async () => {
    try {
      const data = await reportAPI.getScheduledReports();
      setScheduledReports(data.scheduled_reports || []);
    } catch (error) {
      console.warn('Scheduled reports not available yet:', error);
      setScheduledReports([]);
    }
  };

  const handleReportSelect = (report) => {
    setSelectedReport(report);
    setFilters({ 
      ...filters, 
      format: 'pdf',
      comparison_type: 'students'  // ✅ Reset to default
    });
    setShowPreview(false);
    setError(null);
  };

  const handleGenerateReport = async () => {
    if (!selectedReport) {
      alert('Please select a report type');
      return;
    }

    // Validate required parameters
    if (selectedReport.id === 'student_progress' && !filters.student_id) {
      alert('Please select a student');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // ✅ Build params based on comparison type
      const params = { ...filters };
      
      // For comparative analysis, include comparison_type
      if (selectedReport.id === 'comparative_analysis') {
        params.comparison_type = filters.comparison_type || 'students';
      }

      await reportAPI.generateReport(selectedReport.id, filters.format, params);
      alert('✅ Report downloaded successfully!');
    } catch (error) {
      console.error('Report generation error:', error);
      setError('Failed to generate report: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewReport = async () => {
    if (!selectedReport) {
      alert('Please select a report type');
      return;
    }

    if (selectedReport.id === 'student_progress' && !filters.student_id) {
      alert('Please select a student to preview their report');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const preview = await reportAPI.getReportPreview(selectedReport.id, filters);
      setPreviewData(preview);
      setShowPreview(true);
    } catch (error) {
      console.error('Preview error:', error);
      setError('Failed to load preview: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getReportIcon = (reportId) => {
    const icons = {
      'student_progress': Users,
      'class_overview': TrendingUp,
      'module_performance': BookOpen,
      'exercise_analysis': BarChart3,
      'engagement_metrics': Clock,
      'comparative_analysis': PieChart,
      'achievement_summary': Award,
      'weekly_summary': Calendar
    };
    return icons[reportId] || FileText;
  };

  const getFormatIcon = (format) => {
    switch (format) {
      case 'pdf': return FileText;
      case 'excel': return FileSpreadsheet;
      case 'json': return FileJson;
      default: return FileText;
    }
  };

  return (
    <div className="reports-container">
      <div className="section-header">
        <FileText size={28} />
        <h2>Generate Reports</h2>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="btn-close-error">×</button>
        </div>
      )}

      <div className="reports-grid">
        {/* Report Types Selection */}
        <div className="report-types-section">
          <h3>Select Report Type</h3>
          <div className="report-types-grid">
            {reportTypes.map(report => {
              const Icon = getReportIcon(report.id);
              return (
                <div
                  key={report.id}
                  className={`report-type-card ${selectedReport?.id === report.id ? 'selected' : ''}`}
                  onClick={() => handleReportSelect(report)}
                >
                  <Icon size={32} className="report-icon" />
                  <h4>{report.name}</h4>
                  <p>{report.description}</p>
                  <div className="report-formats">
                    {report.formats.map(format => {
                      const FormatIcon = getFormatIcon(format);
                      return (
                        <span key={format} className="format-badge">
                          <FormatIcon size={14} />
                          {format.toUpperCase()}
                        </span>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Report Configuration */}
        {selectedReport && (
          <div className="report-config-section">
            <h3>Configure Report</h3>
            
            {/* ✅ SPECIAL HANDLING FOR COMPARATIVE ANALYSIS */}
            {selectedReport.id === 'comparative_analysis' ? (
              <div className="comparative-analysis-config">
                {/* Comparison Type Selection */}
                <div className="form-group">
                  <label>Comparison Type</label>
                  <select
                    value={filters.comparison_type}
                    onChange={(e) => setFilters({...filters, comparison_type: e.target.value})}
                    className="form-control"
                  >
                    <option value="students">Compare Students</option>
                    <option value="modules">Compare Modules</option>
                    <option value="time">Compare Time Periods</option>
                  </select>
                </div>

                {/* Conditional Filters */}
                {filters.comparison_type === 'students' && (
                  <div className="form-group">
                    <label>Select Students (Optional)</label>
                    <input
                      type="text"
                      placeholder="Enter student IDs separated by comma (e.g., 1,2,3)"
                      value={filters.student_ids || ''}
                      onChange={(e) => setFilters({...filters, student_ids: e.target.value})}
                      className="form-control"
                    />
                    <small>Leave empty to compare all students</small>
                  </div>
                )}

                {filters.comparison_type === 'modules' && (
                  <div className="form-group">
                    <label>Select Modules (Optional)</label>
                    <input
                      type="text"
                      placeholder="Enter module IDs (e.g., module_1,module_2)"
                      value={filters.module_ids || ''}
                      onChange={(e) => setFilters({...filters, module_ids: e.target.value})}
                      className="form-control"
                    />
                    <small>Leave empty to compare all modules</small>
                  </div>
                )}

                {/* Date Range */}
                <div className="form-group">
                  <label>Date Range (Optional)</label>
                  <div className="date-range">
                    <input
                      type="date"
                      value={filters.date_from || ''}
                      onChange={(e) => setFilters({...filters, date_from: e.target.value})}
                      className="form-control"
                    />
                    <span>to</span>
                    <input
                      type="date"
                      value={filters.date_to || ''}
                      onChange={(e) => setFilters({...filters, date_to: e.target.value})}
                      className="form-control"
                    />
                  </div>
                  <small>
                    {filters.comparison_type === 'time' 
                      ? 'Shows weekly performance trends' 
                      : 'Filter data by date range'}
                  </small>
                </div>

                {/* Format Selection */}
                <div className="form-group">
                  <label>Export Format</label>
                  <div className="format-buttons">
                    <button
                      type="button"
                      className={`format-btn ${filters.format === 'pdf' ? 'active' : ''}`}
                      onClick={() => setFilters({...filters, format: 'pdf'})}
                    >
                      <FileText size={16} />
                      PDF
                    </button>
                    <button
                      type="button"
                      className={`format-btn ${filters.format === 'excel' ? 'active' : ''}`}
                      onClick={() => setFilters({...filters, format: 'excel'})}
                    >
                      <FileSpreadsheet size={16} />
                      EXCEL
                    </button>
                    <button
                      type="button"
                      className={`format-btn ${filters.format === 'json' ? 'active' : ''}`}
                      onClick={() => setFilters({...filters, format: 'json'})}
                    >
                      <FileJson size={16} />
                      JSON
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // ✅ OTHER REPORTS USE STANDARD FILTERS
              <ReportFilters
                report={selectedReport}
                filters={filters}
                onFiltersChange={setFilters}
                students={students}
                modules={modules}
              />
            )}

            <div className="report-actions">
              <button
                onClick={handlePreviewReport}
                className="btn btn-secondary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader size={16} className="spinner" />
                    Loading...
                  </>
                ) : (
                  <>
                    <Eye size={16} />
                    Preview
                  </>
                )}
              </button>
              
              <button
                onClick={handleGenerateReport}
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader size={16} className="spinner" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download size={16} />
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Report Preview Modal */}
      {showPreview && (
        <ReportPreview
          reportType={selectedReport}
          data={previewData}
          onClose={() => setShowPreview(false)}
        />
      )}

      {/* Scheduled Reports Section */}
      {scheduledReports.length > 0 && (
        <div className="scheduled-reports-section">
          <h3>
            <Calendar size={24} />
            Scheduled Reports
          </h3>
          <div className="scheduled-reports-list">
            {scheduledReports.map(scheduled => (
              <div key={scheduled.id} className="scheduled-report-card">
                <div className="scheduled-report-header">
                  <strong>{scheduled.report_type.replace('_', ' ').toUpperCase()}</strong>
                  <span className={`status-badge ${scheduled.status}`}>
                    {scheduled.status}
                  </span>
                </div>
                <div className="scheduled-report-details">
                  <p>📅 Schedule: {scheduled.schedule}</p>
                  <p>📧 Recipients: {scheduled.recipients.join(', ')}</p>
                  <p>⏰ Last Run: {scheduled.last_run}</p>
                  <p>⏭️ Next Run: {scheduled.next_run}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}