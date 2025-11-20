// ============================================================================
// COMPLETE UPDATE for UserManagement.jsx with Activity Tracking
// ============================================================================

import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Filter, Plus, Edit, Trash2, 
  Shield, UserCheck, UserX, RefreshCw, Eye,
  Activity, Clock, LogIn  // ✅ NEW icons
} from 'lucide-react';
import { userAPI } from '../../services/api';
import UserDetailModal from './UserDetailModal';
import "../../styles/UserManagement.css";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activityFilter, setActivityFilter] = useState('');  // ✅ NEW
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    loadUsers();
  }, [currentPage, pageSize, searchTerm, roleFilter, statusFilter, activityFilter, sortBy, sortOrder]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await userAPI.listUsers({
        page: currentPage,
        limit: pageSize,
        search: searchTerm,
        role_filter: roleFilter,
        status_filter: statusFilter,
        activity_filter: activityFilter,  // ✅ NEW
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setUsers(data.users || []);
      setTotalPages(data.pagination?.pages || 1);
    } catch (error) {
      console.error('Failed to load users:', error);
      alert('Failed to load users: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ✅ NEW: Activity badge helper
  const getActivityBadge = (status) => {
    const badges = {
      'online': { text: '🟢 Online', color: '#28a745', bg: '#28a74520' },
      'today': { text: '🟡 Today', color: '#ffc107', bg: '#ffc10720' },
      'this_week': { text: '🔵 This Week', color: '#17a2b8', bg: '#17a2b820' },
      'this_month': { text: '🟠 This Month', color: '#fd7e14', bg: '#fd7e1420' },
      'inactive': { text: '⚫ Inactive', color: '#6c757d', bg: '#6c757d20' },
      'never': { text: '⚪ Never', color: '#999', bg: '#99999920' }
    };
    return badges[status] || badges.never;
  };

  // ✅ NEW: Format relative time
  const getRelativeTime = (dateString) => {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const handleViewUser = async (userId) => {
    try {
      const userData = await userAPI.getUserDetail(userId);
      setSelectedUser(userData);
      setShowDetailModal(true);
    } catch (error) {
      alert('Failed to load user details: ' + error.message);
    }
  };

  const handleToggleStatus = async (userId) => {
    if (!confirm('Are you sure you want to toggle this user\'s status?')) return;
    
    try {
      await userAPI.toggleUserStatus(userId);
      loadUsers();
    } catch (error) {
      alert('Failed to toggle user status: ' + error.message);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    
    try {
      await userAPI.deleteUser(userId);
      loadUsers();
    } catch (error) {
      alert('Failed to delete user: ' + error.message);
    }
  };

  return (
    <div className="user-management">
      {/* Header */}
      <div className="section-header">
        <Users size={28} />
        <h2>User Management</h2>
      </div>

      {/* Filters */}
      <div className="filters-container">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>

        <div className="filter-group">
          <label>Role</label>
          <select 
            value={roleFilter} 
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="filter-select"
          >
            <option value="">All Roles</option>
            <option value="student">Students</option>
            <option value="teacher">Teachers</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status</label>
          <select 
            value={statusFilter} 
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="filter-select"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {/* ✅ NEW: Activity Filter */}
        <div className="filter-group">
          <label>
            <Activity size={16} style={{verticalAlign: 'middle'}} />
            Activity
          </label>
          <select 
            value={activityFilter} 
            onChange={(e) => {
              setActivityFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="filter-select"
          >
            <option value="">All Activity</option>
            <option value="active">Active (24h)</option>
            <option value="inactive_7d">Inactive (7d)</option>
            <option value="inactive_30d">Inactive (30d)</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Sort By</label>
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="filter-select"
          >
            <option value="created_at">Created Date</option>
            <option value="username">Username</option>
            <option value="full_name">Full Name</option>
            <option value="last_active">Last Active</option>
            <option value="login_count">Login Count</option>
          </select>
        </div>

        <button 
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="btn btn-secondary btn-icon"
          title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
        >
          {sortOrder === 'asc' ? '↑' : '↓'}
        </button>

        <button 
          onClick={loadUsers} 
          className="btn btn-secondary btn-icon"
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'spinning' : ''} />
        </button>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading users...</p>
        </div>
      ) : users.length > 0 ? (
        <div className="table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>
                  <Activity size={16} style={{verticalAlign: 'middle', marginRight: '4px'}} />
                  Activity
                </th>
                <th>
                  <Clock size={16} style={{verticalAlign: 'middle', marginRight: '4px'}} />
                  Last Seen
                </th>
                <th>
                  <LogIn size={16} style={{verticalAlign: 'middle', marginRight: '4px'}} />
                  Logins
                </th>
                <th>Stats</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => {
                const activityBadge = getActivityBadge(user.activity_status);
                
                return (
                  <tr key={user.id}>
                    {/* User Info */}
                    <td>
                      <div className="user-cell">
                        <div className="user-avatar">
                          {user.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <strong>{user.full_name}</strong>
                          <small>@{user.username}</small>
                        </div>
                      </div>
                    </td>

                    {/* Email */}
                    <td>
                      <small style={{color: '#666'}}>{user.email}</small>
                    </td>

                    {/* Role */}
                    <td>
                      <span className={`role-badge ${user.role}`}>
                        {user.role === 'teacher' ? <Shield size={14} /> : <Users size={14} />}
                        {user.role}
                      </span>
                    </td>

                    {/* Status */}
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? <UserCheck size={14} /> : <UserX size={14} />}
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>

                    {/* ✅ NEW: Activity Status */}
                    <td>
                      <span 
                        className="activity-badge"
                        style={{
                          color: activityBadge.color,
                          background: activityBadge.bg,
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '600',
                          display: 'inline-block'
                        }}
                      >
                        {activityBadge.text}
                      </span>
                    </td>

                    {/* ✅ NEW: Last Seen */}
                    <td>
                      <div style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
                        <Clock size={14} color="#666" />
                        <small style={{color: '#666'}}>
                          {getRelativeTime(user.last_active)}
                        </small>
                      </div>
                    </td>

                    {/* ✅ NEW: Login Count */}
                    <td>
                      <div style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
                        <LogIn size={14} color="#667eea" />
                        <strong style={{color: '#667eea'}}>
                          {user.login_count || 0}
                        </strong>
                      </div>
                    </td>

                    {/* Stats */}
                    <td>
                      <div className="stats-mini">
                        <span title="Modules Completed">
                          📚 {user.statistics?.modules_completed || 0}
                        </span>
                        <span title="Total Score">
                          🏆 {user.statistics?.total_score || 0}
                        </span>
                      </div>
                    </td>

                    {/* Actions */}
                    <td>
                      <div className="action-buttons">
                        <button 
                          onClick={() => handleViewUser(user.id)}
                          className="btn btn-sm btn-primary"
                          title="View Details"
                        >
                          <Eye size={14} />
                        </button>
                        <button 
                          onClick={() => handleToggleStatus(user.id)}
                          className={`btn btn-sm ${user.is_active ? 'btn-warning' : 'btn-success'}`}
                          title={user.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {user.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                        </button>
                        <button 
                          onClick={() => handleDeleteUser(user.id)}
                          className="btn btn-sm btn-danger"
                          title="Delete User"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <Users size={80} color="#ccc" />
          <h3>No Users Found</h3>
          <p>Try adjusting your filters</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="btn btn-secondary"
          >
            Previous
          </button>
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button 
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="btn btn-secondary"
          >
            Next
          </button>
        </div>
      )}

      {/* User Detail Modal */}
      {showDetailModal && selectedUser && (
        <UserDetailModal
          user={selectedUser}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedUser(null);
          }}
          onRefresh={loadUsers}
        />
      )}
    </div>
  );
}