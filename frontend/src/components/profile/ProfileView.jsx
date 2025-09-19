import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import ProfileEdit from './ProfileEdit'

const ProfileView = ({ user, onProfileUpdate }) => {
  const { getUserRole } = useAuth()
  const [isEditing, setIsEditing] = useState(false)

  // Debug: Log when user prop changes
  useEffect(() => {
    console.log('ProfileView received user data:', user)
  }, [user])

  const handleEditComplete = (updatedUser) => {
    console.log('ProfileView handleEditComplete called with:', updatedUser)
    setIsEditing(false)
    if (updatedUser) {
      onProfileUpdate(updatedUser)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified'
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return 'Invalid date'
    }
  }

  const formatJoinDate = (dateString) => {
    if (!dateString) return 'Unknown'
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
      })
    } catch {
      return 'Unknown'
    }
  }

  if (isEditing) {
    return (
      <ProfileEdit
        user={user}
        onProfileUpdate={handleEditComplete}
        onCancel={() => setIsEditing(false)}
      />
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Profile</h2>
        <button
          onClick={() => setIsEditing(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
        >
          Edit Profile
        </button>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {user?.display_name 
                  ? user.display_name.charAt(0).toUpperCase()
                  : user?.first_name 
                    ? user.first_name.charAt(0).toUpperCase()
                    : user?.email?.charAt(0).toUpperCase() || '?'
                }
              </span>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                {user?.display_name || 
                 (user?.first_name && user?.last_name 
                   ? `${user.first_name} ${user.last_name}` 
                   : user?.first_name || 'User')}
              </h3>
              <p className="text-gray-600">{user?.email}</p>
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                Personal Information
              </h4>
              <div className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-700">First Name</dt>
                  <dd className="text-gray-900">{user?.first_name || 'Not specified'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Last Name</dt>
                  <dd className="text-gray-900">{user?.last_name || 'Not specified'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Display Name</dt>
                  <dd className="text-gray-900">{user?.display_name || 'Not specified'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Date of Birth</dt>
                  <dd className="text-gray-900">{formatDate(user?.date_of_birth)}</dd>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                Contact Information
              </h4>
              <div className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-700">Email</dt>
                  <dd className="text-gray-900">{user?.email}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Phone Number</dt>
                  <dd className="text-gray-900">{user?.phone_number || 'Not specified'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Account Role</dt>
                  <dd className="text-gray-900">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      getUserRole() === 'SUPERADMIN' ? 'bg-purple-100 text-purple-800' :
                      getUserRole() === 'ADMIN' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {getUserRole()}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Member Since</dt>
                  <dd className="text-gray-900">{formatJoinDate(user?.created_at)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-700">Email Verified</dt>
                  <dd className="text-gray-900">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user?.is_verified 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {user?.is_verified ? 'Verified' : 'Pending'}
                    </span>
                  </dd>
                </div>
              </div>
            </div>
          </div>
          
          {user?.bio && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                Bio
              </h4>
              <p className="text-gray-900 leading-relaxed">{user.bio}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProfileView
