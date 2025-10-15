import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import RegistrationForm from '../components/RegistrationForm'
import OAuthButtons from '../components/auth/OAuthButtons'

const RegisterPage = () => {
  const { isAuthenticated } = useAuth()
  const [registrationSuccess, setRegistrationSuccess] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/chat/new" replace />
  }

  if (registrationSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-6 text-3xl font-bold text-gray-900">Registration Successful</h2>
            <p className="mt-2 text-sm text-gray-600">
              We've sent a verification email to your address. Please check your inbox and click the verification link to activate your account.
            </p>
            <div className="mt-6">
              <Link
                to="/login"
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
              >
                Return to Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">Create your account</h2>
          <p className="mt-2 text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
        
        <div className="mt-8">
          <OAuthButtons 
            onLoading={(loading) => {
              // Handle loading state if needed
            }}
          />
        </div>
        
        <RegistrationForm onSuccess={() => setRegistrationSuccess(true)} />
        
        <div className="text-xs text-gray-500 text-center">
          By creating an account, you agree to our Terms of Service and Privacy Policy.
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
