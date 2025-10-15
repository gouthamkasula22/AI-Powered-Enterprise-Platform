import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

const VerifyEmailPage = () => {
  const { token } = useParams()
  const navigate = useNavigate()
  const { verifyEmail, refreshUserData, isAuthenticated } = useAuth()
  const [verificationStatus, setVerificationStatus] = useState('verifying')
  const [error, setError] = useState('')
  const processedTokenRef = useRef(null)

  useEffect(() => {
    if (token && processedTokenRef.current !== token) {
      processedTokenRef.current = token
      verifyEmailToken(token)
    }
  }, [token])

  const verifyEmailToken = async (verificationToken) => {
    try {
      const result = await verifyEmail(verificationToken)
      if (result.success) {
        setVerificationStatus('success')
        
        // Refresh user data if user is logged in
        if (isAuthenticated) {
          await refreshUserData()
          // Don't show toast here since AuthContext already shows it
          // If user is already logged in, redirect to chat
          setTimeout(() => navigate('/chat/new'), 2000)
        } else {
          // If not logged in, redirect to login
          setTimeout(() => navigate('/login'), 3000)
        }
      } else {
        setVerificationStatus('error')
        setError(result.error || 'Verification failed')
        // Don't show toast here since AuthContext already shows it
      }
    } catch (error) {
      setVerificationStatus('error')
      setError('Verification failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          {verificationStatus === 'verifying' && (
            <div>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <h2 className="mt-4 text-2xl font-bold">Verifying Email...</h2>
            </div>
          )}

          {verificationStatus === 'success' && (
            <div>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="mt-4 text-2xl font-bold text-green-600">Email Verified!</h2>
              <p className="mt-2 text-gray-600">
                {isAuthenticated ? 'Redirecting to chat...' : 'Redirecting to login...'}
              </p>
            </div>
          )}

          {verificationStatus === 'error' && (
            <div>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="mt-4 text-2xl font-bold text-red-600">Verification Failed</h2>
              <p className="mt-2 text-gray-600">{error}</p>
              <button 
                onClick={() => navigate('/login')}
                className="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Back to Login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VerifyEmailPage
