import React from 'react';
import { Filter, Users, BookOpen, Calendar, FileText } from 'lucide-react';

export default function ReportFilters({ report, filters, onFiltersChange, students, modules }) {
  /**
   * Report Filters Component
   * Dynamic filters based on report type requirements
   */

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const renderFilters = () => {
    if (!report) return null;

    const requiredParams = report.parameters || [];

    return (
      <div className="report-filters">
        <div className="filter-header">
          <Filter size={20} />
          <h4>Report Parameters</h4>
        </div>

        {/* Student Selection (if required) */}
        {requiredParams.includes('student_id') && (
          <div className="filter-group">
            <label>
              <Users size={16} />
              Select Student *
            </label>
            <select
              value={filters.student_id || ''}
              onChange={(e) => handleFilterChange('student_id', e.target.value)}
              required
            >
              <option value="">-- Select Student --</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>
                  {student.full_name} (@{student.username})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Module Selection (if required) */}
        {requiredParams.includes('module_id (optional)') && (
          <div className="filter-group">
            <label>
              <BookOpen size={16} />
              Select Module (Optional)
            </label>
            <select
              value={filters.module_id || ''}
              onChange={(e) => handleFilterChange('module_id', e.target.value || null)}
            >
              <option value="">-- All Modules --</option>
              {modules.map(module => (
                <option key={module.id} value={module.id}>
                  {module.classic_text.substring(0, 60)}...
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Date Range (if required) */}
        {(requiredParams.includes('date_from') || requiredParams.includes('date_to')) && (
          <div className="filter-group">
            <label>
              <Calendar size={16} />
              Date Range
            </label>
            <div className="date-range-inputs">
              <input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                placeholder="From"
              />
              <span className="date-separator">to</span>
              <input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                placeholder="To"
              />
            </div>
          </div>
        )}

        {/* Output Format Selection (always shown) */}
        <div className="filter-group">
          <label>
            <FileText size={16} />
            Output Format
          </label>
          <div className="format-options">
            {(report.formats || ['pdf', 'excel', 'json']).map(format => (
              <label key={format} className="format-option">
                <input
                  type="radio"
                  name="format"
                  value={format}
                  checked={filters.format === format}
                  onChange={(e) => handleFilterChange('format', e.target.value)}
                />
                <span className="format-label">
                  {format === 'pdf' && '📄 PDF'}
                  {format === 'excel' && '📊 Excel'}
                  {format === 'json' && '📋 JSON'}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Week Offset (for weekly summary) */}
        {requiredParams.includes('week_offset') && (
          <div className="filter-group">
            <label>
              <Calendar size={16} />
              Week Selection
            </label>
            <select
              value={filters.week_offset || '0'}
              onChange={(e) => handleFilterChange('week_offset', e.target.value)}
            >
              <option value="0">Current Week</option>
              <option value="1">Last Week</option>
              <option value="2">2 Weeks Ago</option>
              <option value="3">3 Weeks Ago</option>
              <option value="4">4 Weeks Ago</option>
            </select>
          </div>
        )}

        {/* Analysis Type (for comparative analysis) */}
        {requiredParams.includes('analysis_type') && (
          <div className="filter-group">
            <label>
              <Filter size={16} />
              Analysis Type
            </label>
            <select
              value={filters.analysis_type || ''}
              onChange={(e) => handleFilterChange('analysis_type', e.target.value)}
            >
              <option value="">-- Select Type --</option>
              <option value="students">Compare Students</option>
              <option value="modules">Compare Modules</option>
              <option value="time_periods">Compare Time Periods</option>
            </select>
          </div>
        )}

        {/* Entity IDs (for comparative analysis) */}
        {requiredParams.includes('entity_ids') && filters.analysis_type && (
          <div className="filter-group">
            <label>
              <Filter size={16} />
              Select Items to Compare
            </label>
            {filters.analysis_type === 'students' && (
              <select
                multiple
                size="5"
                value={filters.entity_ids || []}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  handleFilterChange('entity_ids', selected);
                }}
              >
                {students.map(student => (
                  <option key={student.id} value={student.id}>
                    {student.full_name}
                  </option>
                ))}
              </select>
            )}
            {filters.analysis_type === 'modules' && (
              <select
                multiple
                size="5"
                value={filters.entity_ids || []}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  handleFilterChange('entity_ids', selected);
                }}
              >
                {modules.map(module => (
                  <option key={module.id} value={module.id}>
                    {module.classic_text.substring(0, 50)}...
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="report-filters-container">
      {renderFilters()}
      
      {report && (
        <div className="filter-info">
          <p className="filter-description">
            <strong>Report Description:</strong> {report.description}
          </p>
          {report.parameters && report.parameters.length > 0 && (
            <p className="filter-parameters">
              <strong>Required Parameters:</strong> {report.parameters.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}