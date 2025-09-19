import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const HomePage = () => {
  const { isAuthenticated, user } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            User Authentication System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Secure, modern authentication with JWT and email verification
          </p>
          
          {isAuthenticated ? (
            <div className="space-y-4">
              <p className="text-lg text-gray-700">
                Welcome back, {user?.first_name || user?.email}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link 
                  to="/dashboard" 
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
                >
                  Go to Dashboard
                </Link>
                
                {/* Admin Navigation */}
                {(user?.role === 'ADMIN' || user?.role === 'SUPERADMIN') && (
                  <>
                    <Link 
                      to="/admin" 
                      className="inline-block bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
                    >
                      Admin Dashboard
                    </Link>
                    <Link 
                      to="/admin/users" 
                      className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
                    >
                      Manage Users
                    </Link>
                  </>
                )}
              </div>
              
              {/* Role Display */}
              <div className="mt-4">
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                  user?.role === 'SUPERADMIN' ? 'bg-purple-100 text-purple-800' :
                  user?.role === 'ADMIN' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  Role: {user?.role || 'USER'}
                </span>
              </div>
            </div>
          ) : (
            <div className="space-x-4">
              <Link 
                to="/login" 
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
              >
                Sign In
              </Link>
              <Link 
                to="/register" 
                className="inline-block bg-white hover:bg-gray-50 text-blue-600 font-medium py-2 px-6 rounded-md border border-blue-600 transition-colors"
              >
                Create Account
              </Link>
            </div>
          )}
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="card text-center">
            <h3 className="text-lg font-semibold mb-2">🔐 Secure Authentication</h3>
            <p className="text-gray-600">JWT tokens with Argon2 password hashing</p>
          </div>
          <div className="card text-center">
            <h3 className="text-lg font-semibold mb-2">🚀 Social Login</h3>
            <p className="text-gray-600">Google, Facebook, and LinkedIn integration</p>
          </div>
          <div className="card text-center">
            <h3 className="text-lg font-semibold mb-2">📱 Responsive Design</h3>
            <p className="text-gray-600">Modern UI with Tailwind CSS</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
