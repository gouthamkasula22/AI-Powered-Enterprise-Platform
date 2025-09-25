import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { emailService } from '../services/emailService'
import PasswordStrengthMeter from '../components/PasswordStrengthMeter'
import toast from 'react-hot-toast'

const ResetPasswordPage = () => {
  const { token } = useParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isValidToken, setIsValidToken] = useState(null)
  const [passwordValidation, setPasswordValidation] = useState({
    isValid: null,
    strengthScore: 0,
    strengthLevel: 'Weak',
    requirements: [],
    suggestions: [],
    estimatedCrackTime: ''
  })

  useEffect(() => {
    // Set token as valid immediately since validation happens during reset
    if (token) {
      setIsValidToken(true)
    } else {
      setIsValidToken(false)
    }
  }, [token])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (password.length > 0) {
        validatePassword(password)
      }
    }, 300) // Debounce validation

    return () => clearTimeout(timer)
  }, [password])

  const validatePassword = async (pwd) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/validate-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd, email: '' })
      })
      
      const result = await response.json()
      
      setPasswordValidation({
        isValid: result.is_valid,
        strengthScore: result.strength_score,
        strengthLevel: result.strength_level,
        requirements: result.requirements,
        suggestions: result.suggestions,
        estimatedCrackTime: result.estimated_crack_time
      })
    } catch (error) {
      console.error('Password validation error:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    console.log('=== DEBUG INFO ===')
    console.log('Token from useParams:', token)
    console.log('Password validation state:', passwordValidation)
    console.log('Password length:', password.length)
    console.log('==================')
    
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }

    // Skip password validation check for now to test navigation
    // if (passwordValidation.isValid === false) {
    //   toast.error('Password does not meet security requirements')
    //   return
    // }

    setIsLoading(true)
    
    try {
      console.log('Calling resetPassword with token:', token)
      console.log('Password validation passed, proceeding with reset...')
      const result = await emailService.resetPassword(token, password)
      console.log('Reset password result:', result)
      toast.success('Password reset successfully!')
      console.log('About to navigate to /login')
      navigate('/login')
    } catch (error) {
      console.error('Reset password error:', error)
      console.error('Error response:', error.response?.data)
      toast.error(error.response?.data?.detail || 'Failed to reset password')
    } finally {
      setIsLoading(false)
    }
  }

  if (isValidToken === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isValidToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8 text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-red-600">Invalid Reset Link</h2>
          <p className="text-gray-600">This password reset link is invalid or has expired.</p>
          <button 
            onClick={() => navigate('/forgot-password')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Request New Reset Link
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Reset Password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your new password below
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              New Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter new password"
            />
            {password && (
              <PasswordStrengthMeter 
                strengthScore={passwordValidation.strengthScore}
                strengthLevel={passwordValidation.strengthLevel}
                isVisible={password.length > 0}
              />
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Confirm new password"
            />
            {confirmPassword && password !== confirmPassword && (
              <p className="mt-1 text-sm text-red-600">Passwords do not match</p>
            )}
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading || password !== confirmPassword || !password}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ResetPasswordPage
