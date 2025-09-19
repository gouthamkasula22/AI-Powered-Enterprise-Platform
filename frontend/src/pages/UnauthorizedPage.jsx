import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const UnauthorizedPage = () => {
  const navigate = useNavigate()
  const { user, getUserRole } = useAuth()

  const handleGoBack = () => {
    navigate(-1)
  }

  const handleGoHome = () => {
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            {/* Warning Icon */}
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
            </div>

            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              Access Denied
            </h2>
            
            <p className="mt-2 text-sm text-gray-600">
              You don't have permission to access this resource.
            </p>

            {user && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md">
                <p className="text-xs text-gray-500">
                  Current Role: <span className="font-medium text-gray-700">{getUserRole()}</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  User: <span className="font-medium text-gray-700">{user.email}</span>
                </p>
              </div>
            )}

            <div className="mt-6 flex flex-col space-y-3">
              <button
                onClick={handleGoBack}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Go Back
              </button>
              
              <button
                onClick={handleGoHome}
                className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Go to Dashboard
              </button>
            </div>

            <div className="mt-6 text-center">
              <p className="text-xs text-gray-500">
                If you believe this is an error, please contact your administrator.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UnauthorizedPage