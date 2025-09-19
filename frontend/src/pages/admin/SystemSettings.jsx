import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

const SystemSettings = () => {
  const [settings, setSettings] = useState({
    allowRegistration: true,
    requireEmailVerification: true,
    sessionTimeout: 24,
    maxLoginAttempts: 5,
    passwordMinLength: 8,
    enableOAuth: true,
    maintenanceMode: false,
    systemName: 'User Auth System',
    adminEmail: 'admin@example.com'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    fetchSystemSettings()
  }, [])

  const fetchSystemSettings = async () => {
    try {
      setIsLoading(true)
      // Mock API call - replace with actual implementation
      // const response = await axios.get('/api/v1/admin/system/settings')
      // setSettings(response.data)
    } catch (error) {
      console.error('Failed to fetch system settings:', error)
      toast.error('Failed to load system settings')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true)
      // Mock API call - replace with actual implementation
      // await axios.put('/api/v1/admin/system/settings', settings)
      toast.success('System settings updated successfully')
    } catch (error) {
      console.error('Failed to save system settings:', error)
      toast.error('Failed to save system settings')
    } finally {
      setIsSaving(false)
    }
  }

  const handleInputChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const SettingCard = ({ title, description, children }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600 mt-1">{description}</p>
      </div>
      {children}
    </div>
  )

  const ToggleSwitch = ({ enabled, onToggle, label, description }) => (
    <div className="flex items-center justify-between">
      <div className="flex-grow">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      <button
        type="button"
        className={`${
          enabled ? 'bg-blue-600' : 'bg-gray-200'
        } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`}
        onClick={() => onToggle(!enabled)}
      >
        <span
          className={`${
            enabled ? 'translate-x-5' : 'translate-x-0'
          } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
        />
      </button>
    </div>
  )

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
              <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
              <p className="text-sm text-gray-600 mt-1">
                Configure system-wide settings and security policies
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleSaveSettings}
                disabled={isSaving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              <Link
                to="/admin"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Back to Admin Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Authentication Settings */}
          <SettingCard
            title="Authentication"
            description="Configure user registration and login settings"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={settings.allowRegistration}
                onToggle={(value) => handleInputChange('allowRegistration', value)}
                label="Allow User Registration"
                description="Enable new users to register accounts"
              />
              
              <ToggleSwitch
                enabled={settings.requireEmailVerification}
                onToggle={(value) => handleInputChange('requireEmailVerification', value)}
                label="Require Email Verification"
                description="Users must verify their email before accessing the system"
              />
              
              <ToggleSwitch
                enabled={settings.enableOAuth}
                onToggle={(value) => handleInputChange('enableOAuth', value)}
                label="Enable OAuth Login"
                description="Allow login with Google, GitHub, etc."
              />
            </div>
          </SettingCard>

          {/* Security Settings */}
          <SettingCard
            title="Security"
            description="Configure security policies and password requirements"
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Session Timeout (hours)
                </label>
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={settings.sessionTimeout}
                  onChange={(e) => handleInputChange('sessionTimeout', parseInt(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Max Login Attempts
                </label>
                <input
                  type="number"
                  min="3"
                  max="10"
                  value={settings.maxLoginAttempts}
                  onChange={(e) => handleInputChange('maxLoginAttempts', parseInt(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Minimum Password Length
                </label>
                <input
                  type="number"
                  min="6"
                  max="20"
                  value={settings.passwordMinLength}
                  onChange={(e) => handleInputChange('passwordMinLength', parseInt(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </SettingCard>

          {/* System Configuration */}
          <SettingCard
            title="System Configuration"
            description="General system settings and information"
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  System Name
                </label>
                <input
                  type="text"
                  value={settings.systemName}
                  onChange={(e) => handleInputChange('systemName', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Admin Email
                </label>
                <input
                  type="email"
                  value={settings.adminEmail}
                  onChange={(e) => handleInputChange('adminEmail', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <ToggleSwitch
                enabled={settings.maintenanceMode}
                onToggle={(value) => handleInputChange('maintenanceMode', value)}
                label="Maintenance Mode"
                description="Temporarily disable system access for maintenance"
              />
            </div>
          </SettingCard>

          {/* System Information */}
          <SettingCard
            title="System Information"
            description="Current system status and statistics"
          >
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">System Version:</span>
                <span className="font-medium">v1.0.0</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Database Status:</span>
                <span className="font-medium text-green-600">Connected</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Email Service:</span>
                <span className="font-medium text-green-600">Operational</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Last Backup:</span>
                <span className="font-medium">2024-01-21 03:00 UTC</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Server Uptime:</span>
                <span className="font-medium">15 days, 4 hours</span>
              </div>
            </div>
          </SettingCard>
        </div>

        {/* Danger Zone */}
        <div className="mt-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-900 mb-2">Danger Zone</h3>
            <p className="text-sm text-red-700 mb-4">
              These actions can have significant impact on the system. Use with caution.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                onClick={() => toast.error('Feature not implemented')}
              >
                Reset All Settings
              </button>
              <button
                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                onClick={() => toast.error('Feature not implemented')}
              >
                Export System Data
              </button>
              <button
                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                onClick={() => toast.error('Feature not implemented')}
              >
                Clear All Sessions
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemSettings