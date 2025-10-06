import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'

const AdminDashboard = () => {
  const { user, getUserRole, isSuperAdmin } = useAuth()
  const [stats, setStats] = useState({
    total_users: 0,
    active_users: 0,
    verified_users: 0,
    admin_users: 0,
    users_today: 0,
    users_this_week: 0
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null) // Add error state

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/admin/users/stats`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      setStats(response.data)
      setError(null)
    } catch (error) {
      console.error('❌ Failed to fetch dashboard stats:')
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        headers: error.config?.headers
      })
      setError(`API Error: ${error.response?.status || 'Network Error'} - ${error.response?.data?.detail || error.message}`)
      // Fallback to mock data

      setStats({
        total_users: 125,
        active_users: 98,
        verified_users: 85,
        admin_users: 5,
        users_today: 3,
        users_this_week: 12
      })
    } finally {
      setIsLoading(false)
    }
  }

  const StatCard = ({ title, value, subtitle, color = 'blue' }) => {
    const colorClasses = {
      blue: 'border-blue-200 bg-blue-50',
      green: 'border-green-200 bg-green-50',
      yellow: 'border-yellow-200 bg-yellow-50',
      red: 'border-red-200 bg-red-50',
      purple: 'border-purple-200 bg-purple-50'
    }

    return (
      <div className={`border rounded-lg p-6 ${colorClasses[color]}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
          </div>
        </div>
      </div>
    )
  }

  const ActionCard = ({ title, description, buttonText, href, icon, color = 'blue' }) => {
    const colorClasses = {
      blue: 'text-blue-600 bg-blue-600 hover:bg-blue-700',
      green: 'text-green-600 bg-green-600 hover:bg-green-700',
      purple: 'text-purple-600 bg-purple-600 hover:bg-purple-700'
    }

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg bg-gray-50 ${colorClasses[color].split(' ')[0]}`}>
              {icon}
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <Link
            to={href}
            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${colorClasses[color].split(' ').slice(1).join(' ')} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${color}-500 transition-colors`}
          >
            {buttonText}
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">
                Welcome back, {user?.first_name} ({getUserRole()})
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {error && (
                <div className="text-sm text-red-600 bg-red-50 px-3 py-1 rounded">
                  {error}
                </div>
              )}
              <Link
                to="/dashboard"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Back to User Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Users"
            value={stats.total_users}
            subtitle="Registered accounts"
            color="blue"
          />
          <StatCard
            title="Active Users"
            value={stats.active_users}
            subtitle="Active accounts"
            color="green"
          />
          <StatCard
            title="Verified Users"
            value={stats.verified_users}
            subtitle="Email verified accounts"
            color="green"
          />
          <StatCard
            title="Admin Users"
            value={stats.admin_users}
            subtitle="Admin & Super Admin accounts"
            color="purple"
          />
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <StatCard
            title="New Users Today"
            value={stats.users_today}
            subtitle="Registered today"
            color="blue"
          />
          <StatCard
            title="New Users This Week"
            value={stats.users_this_week}
            subtitle="Registered this week"
            color="blue"
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <ActionCard
              title="User Management"
              description="View, edit, and manage user accounts"
              buttonText="Manage Users"
              href="/admin/users"
              color="blue"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                </svg>
              }
            />

            {isSuperAdmin() && (
              <ActionCard
                title="System Settings"
                description="Configure system-wide settings and security"
                buttonText="System Config"
                href="/admin/system"
                color="purple"
                icon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m0 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3 0H1.5m8.25-12H15m5.25 0H22.5m-7.5 0a3 3 0 11-6 0 3 3 0 016 0zm0 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                }
              />
            )}

            <ActionCard
              title="Reports"
              description="Generate and view system reports"
              buttonText="View Reports"
              href="/admin/reports"
              color="green"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              }
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-sm font-medium text-gray-900">System Events</h3>
            </div>
            <div className="px-6 py-4">
              <div className="space-y-3">
                <div className="flex items-center text-sm">
                  <div className="flex-shrink-0 w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                  <span className="text-gray-600">New user registration: user@example.com</span>
                  <span className="ml-auto text-gray-400">2 minutes ago</span>
                </div>
                <div className="flex items-center text-sm">
                  <div className="flex-shrink-0 w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
                  <span className="text-gray-600">Password reset request processed</span>
                  <span className="ml-auto text-gray-400">15 minutes ago</span>
                </div>
                <div className="flex items-center text-sm">
                  <div className="flex-shrink-0 w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                  <span className="text-gray-600">Email verification completed</span>
                  <span className="ml-auto text-gray-400">1 hour ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard