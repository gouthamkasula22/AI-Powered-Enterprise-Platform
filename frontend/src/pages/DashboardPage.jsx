import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import EmailVerificationStatus from '../components/auth/EmailVerificationStatus'
import ProfileView from '../components/profile/ProfileView'
import DashboardChatContainer from '../components/chat/DashboardChatContainer'

// Simple NotificationCenter component
const NotificationCenter = () => {
  return (
    <div className="relative">
      <button className="text-gray-500 hover:text-gray-700">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      </button>
    </div>
  );
};

// Simple RoleGuard component
const RoleGuard = ({ children, requireRole }) => {
  const { user } = useAuth();
  const userRole = user?.role || 'user';
  
  // Simple role hierarchy
  const roles = {
    'superadmin': 3,
    'admin': 2,
    'user': 1
  };
  
  if (roles[userRole] >= roles[requireRole]) {
    return children;
  }
  
  return null;
};

// Simple ChangePassword component
const ChangePassword = () => {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
          Current Password
        </label>
        <input
          type="password"
          id="currentPassword"
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <div>
        <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
          New Password
        </label>
        <input
          type="password"
          id="newPassword"
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
          Confirm New Password
        </label>
        <input
          type="password"
          id="confirmPassword"
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
        Change Password
      </button>
    </div>
  );
};

const DashboardPage = () => {
  const { user, refreshUserData, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  // Refresh user data when dashboard loads to ensure we have latest verification status
  useEffect(() => {
    const refreshData = async () => {
      await refreshUserData();
    }
    refreshData();
  }, [refreshUserData]); // Include refreshUserData in dependencies
  
  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };
  
  // Get user role
  const getUserRole = () => {
    return user?.role || 'user';
  };
  
  // Handle profile update
  const handleProfileUpdate = async (profileData) => {
    try {
      // Refresh user data after profile update
      await refreshUserData();
      // Show success message or perform additional actions
    } catch (error) {
      console.error('Profile update error:', error);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'chat', name: 'Chat Assistant', icon: '💬' },
    { id: 'profile', name: 'Profile', icon: '👤' },
    { id: 'security', name: 'Security', icon: '🔒' },
    { id: 'settings', name: 'Settings', icon: '⚙️' }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Authentication System
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <NotificationCenter />
              
              {/* Role Badge */}
              <div className="flex items-center space-x-2">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  getUserRole() === 'superadmin' ? 'bg-purple-100 text-purple-800' :
                  getUserRole() === 'admin' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {getUserRole().toUpperCase()}
                </span>
                
                <RoleGuard requireRole="admin">
                  <Link
                    to="/admin"
                    className="text-sm text-blue-600 hover:text-blue-900 transition-colors"
                  >
                    Admin Panel
                  </Link>
                </RoleGuard>
              </div>
              
              <span className="text-sm text-gray-700">
                Welcome, {user?.first_name || user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-md text-sm font-medium transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Email Verification Status */}
        {user && <EmailVerificationStatus user={user} />}
        
        <div className="flex gap-8">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <nav className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="space-y-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 text-left rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="mr-3 text-base">{tab.icon}</span>
                    {tab.name}
                  </button>
                ))}
              </div>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {activeTab === 'overview' && (
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <h3 className="text-lg font-semibold text-blue-900 mb-2">Account Status</h3>
                      <p className="text-blue-700">
                        {(user?.is_verified || user?.user?.is_verified) ? 'Verified' : 'Pending Verification'}
                      </p>
                    </div>
                    
                    <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                      <h3 className="text-lg font-semibold text-green-900 mb-2">User Role</h3>
                      <p className="text-green-700">{getUserRole()}</p>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Last Login</h3>
                      <p className="text-gray-700">Today</p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <button 
                          onClick={() => setActiveTab('profile')}
                          className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <h4 className="font-medium text-gray-900">Update Profile</h4>
                          <p className="text-sm text-gray-600 mt-1">Manage your personal information</p>
                        </button>
                        <button 
                          onClick={() => setActiveTab('security')}
                          className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <h4 className="font-medium text-gray-900">Security Settings</h4>
                          <p className="text-sm text-gray-600 mt-1">Change password and security options</p>
                        </button>
                        
                        <button 
                          onClick={() => setActiveTab('chat')}
                          className="p-4 text-left border border-purple-200 rounded-lg hover:bg-purple-50 transition-colors"
                        >
                          <h4 className="font-medium text-purple-900">AI Assistant</h4>
                          <p className="text-sm text-purple-600 mt-1">Chat with AI assistant</p>
                        </button>
                        
                        <Link
                          to="/chat/new"
                          className="p-4 text-left border border-orange-200 rounded-lg hover:bg-orange-50 transition-colors"
                        >
                          <h4 className="font-medium text-orange-900">Claude-Style Chat</h4>
                          <p className="text-sm text-orange-600 mt-1">Try our new Claude-style interface</p>
                        </Link>
                        
                        <RoleGuard requireRole="admin">
                          <Link
                            to="/admin"
                            className="p-4 text-left border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                          >
                            <h4 className="font-medium text-blue-900">Admin Dashboard</h4>
                            <p className="text-sm text-blue-600 mt-1">Manage users and system settings</p>
                          </Link>
                        </RoleGuard>
                        
                        <RoleGuard requireRole="admin">
                          <Link
                            to="/admin/users"
                            className="p-4 text-left border border-green-200 rounded-lg hover:bg-green-50 transition-colors"
                          >
                            <h4 className="font-medium text-green-900">User Management</h4>
                            <p className="text-sm text-green-600 mt-1">View and manage user accounts</p>
                          </Link>
                        </RoleGuard>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'chat' && (
                <div className="h-[calc(100vh-12rem)]">
                  <div className="text-center py-10">
                    <h3 className="text-2xl font-medium mb-4">Chat Assistant</h3>
                    <p className="text-gray-600 mb-6">Experience our new Claude-style chat interface</p>
                    <Link to="/chat/new" className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                      <span className="material-icons-outlined text-xl mr-2">chat</span>
                      Open Chat Assistant
                    </Link>
                  </div>
                </div>
              )}

              {activeTab === 'profile' && (
                <ProfileView 
                  user={user} 
                  onProfileUpdate={handleProfileUpdate}
                />
              )}

              {activeTab === 'security' && (
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Security Settings</h2>
                  <ChangePassword />
                </div>
              )}

              {activeTab === 'settings' && (
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Account Settings</h2>
                  
                  <div className="space-y-6">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Notifications</h3>
                      <div className="space-y-3">
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" defaultChecked />
                          <span className="ml-2 text-gray-700">Email notifications</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" defaultChecked />
                          <span className="ml-2 text-gray-700">Security alerts</span>
                        </label>
                      </div>
                    </div>
                    
                    <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                      <h3 className="text-lg font-semibold text-red-900 mb-2">Danger Zone</h3>
                      <p className="text-red-700 mb-4">
                        Once you delete your account, there is no going back. Please be certain.
                      </p>
                      <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
