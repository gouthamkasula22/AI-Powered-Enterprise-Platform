// Home page component
import { Link } from 'react-router-dom'

const HomePage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-gray-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            User Authentication System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Secure, modern authentication with JWT and OAuth integration
          </p>
          
          <div className="space-x-4">
            <Link 
              to="/login" 
              className="btn-primary inline-block"
            >
              Login
            </Link>
            <Link 
              to="/register" 
              className="btn-secondary inline-block"
            >
              Register
            </Link>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="card text-center">
            <h3 className="text-lg font-semibold mb-2">🔐 Secure Authentication</h3>
            <p className="text-gray-600">JWT tokens with bcrypt password hashing</p>
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
