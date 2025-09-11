import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const EmailVerificationStatus = ({ user, onVerificationUpdate }) => {
  const [isResending, setIsResending] = useState(false)
  const { resendVerification } = useAuth()

  const handleResendVerification = async () => {
    setIsResending(true)
    try {
      const userEmail = user.user?.email || user.email
      
      if (!userEmail) {
        toast.error('User email not found')
        return
      }
      
      const result = await resendVerification(userEmail)
      if (result.success) {
        toast.success('Verification email sent!')
      } else {
        toast.error(result.error || 'Failed to send verification email')
      }
    } catch (error) {
      console.error('Resend verification error:', error)
      toast.error('Failed to send verification email')
    } finally {
      setIsResending(false)
    }
  }

  if (user.user?.is_verified || user.is_verified) {
    return null // Don't show if already verified
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Email Verification Required
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>Please check your email and click the verification link to activate your account.</p>
          </div>
          <div className="mt-4">
            <button
              type="button"
              onClick={handleResendVerification}
              disabled={isResending}
              className="bg-yellow-100 px-3 py-2 rounded-md text-sm font-medium text-yellow-800 hover:bg-yellow-200 disabled:opacity-50"
            >
              {isResending ? 'Sending...' : 'Resend Verification Email'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmailVerificationStatus
