# Frontend Email Features Implementation Plan

## 📋 Overview
Complete implementation plan for frontend email features including email verification, password reset flow, and user notifications. This builds on the completed backend email system.

## 🎯 Implementation Phases

### **Phase 1: Email Verification Page** 
**Goal**: Handle email verification links from user emails

#### **1.1 Email Verification Page Component**
**File**: `src/pages/VerifyEmailPage.jsx`
```jsx
// Key Features:
- Parse verification token from URL parameters
- Call backend verification API
- Display success/error messages
- Auto-redirect to login on success
- Resend verification option
```

#### **1.2 Email Verification Service**
**File**: `src/services/emailService.js`
```javascript
// API Methods:
- verifyEmail(token)
- resendVerificationEmail(email)
- checkVerificationStatus(email)
```

#### **1.3 Verification Status Component**
**File**: `src/components/auth/EmailVerificationStatus.jsx`
```jsx
// Features:
- Show verification pending banner
- Resend verification button
- Real-time status updates
```

#### **1.4 Route Integration**
- Add `/verify-email/:token` route
- Update AppRoutes.jsx
- Handle deep linking

---

### **Phase 2: Password Reset Flow**
**Goal**: Complete forgot password and reset forms

#### **2.1 Forgot Password Page**
**File**: `src/pages/ForgotPasswordPage.jsx`
```jsx
// Features:
- Email input form
- Form validation
- Rate limiting display
- Success confirmation
- Back to login link
```

#### **2.2 Reset Password Page**
**File**: `src/pages/ResetPasswordPage.jsx`
```jsx
// Features:
- Parse reset token from URL
- New password form with validation
- Password strength meter integration
- Token expiration handling
- Success redirect to login
```

#### **2.3 Password Reset Service**
**File**: `src/services/passwordResetService.js`
```javascript
// API Methods:
- requestPasswordReset(email)
- validateResetToken(token)
- resetPassword(token, newPassword)
- checkTokenExpiration(token)
```

#### **2.4 Enhanced Form Components**
**File**: `src/components/auth/PasswordResetForm.jsx`
```jsx
// Features:
- Multi-step form (email → confirmation)
- Loading states
- Error handling
- Form validation
- Progress indicators
```

---

### **Phase 3: User Notifications System**
**Goal**: Display security alerts and email notifications in UI

#### **3.1 Notification Context**
**File**: `src/contexts/NotificationContext.jsx`
```jsx
// Features:
- Global notification state
- Real-time updates
- Notification history
- Mark as read functionality
- Auto-dismiss timers
```

#### **3.2 Security Alert Components**
**File**: `src/components/notifications/SecurityAlerts.jsx`
```jsx
// Features:
- New device login alerts
- Suspicious activity warnings
- Account security recommendations
- Action buttons (secure account, etc.)
```

#### **3.3 Notification Bell/Dropdown**
**File**: `src/components/common/NotificationCenter.jsx`
```jsx
// Features:
- Bell icon with unread count
- Dropdown notification list
- Mark all as read
- Notification filtering
- Real-time updates
```

#### **3.4 Email Status Dashboard**
**File**: `src/components/dashboard/EmailStatusCard.jsx`
```jsx
// Features:
- Email verification status
- Recent security alerts
- Email preferences
- Resend verification option
```

---

## 🛠 Detailed Implementation Steps

### **Step 1: Setup API Service Layer**

#### **1.1 Create Base API Service**
**File**: `src/services/api.js`
```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

#### **1.2 Email Service Implementation**
**File**: `src/services/emailService.js`
```javascript
import apiClient from './api'

export const emailService = {
  // Email verification
  async verifyEmail(token) {
    const response = await apiClient.post('/api/v1/auth/verify-email', { token })
    return response.data
  },

  async resendVerificationEmail(email) {
    const response = await apiClient.post('/api/v1/auth/resend-verification', { email })
    return response.data
  },

  // Password reset
  async requestPasswordReset(email) {
    const response = await apiClient.post('/api/v1/auth/forgot-password', { email })
    return response.data
  },

  async validateResetToken(token) {
    const response = await apiClient.post('/api/v1/auth/validate-reset-token', { token })
    return response.data
  },

  async resetPassword(token, newPassword) {
    const response = await apiClient.post('/api/v1/auth/reset-password', { 
      token, 
      new_password: newPassword 
    })
    return response.data
  }
}
```

### **Step 2: Email Verification Implementation**

#### **2.1 Verification Page Component**
**File**: `src/pages/VerifyEmailPage.jsx`
```jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { emailService } from '../services/emailService'
import toast from 'react-hot-toast'

const VerifyEmailPage = () => {
  const { token } = useParams()
  const navigate = useNavigate()
  const [verificationStatus, setVerificationStatus] = useState('verifying')
  const [error, setError] = useState('')

  useEffect(() => {
    if (token) {
      verifyEmailToken(token)
    }
  }, [token])

  const verifyEmailToken = async (verificationToken) => {
    try {
      await emailService.verifyEmail(verificationToken)
      setVerificationStatus('success')
      toast.success('Email verified successfully!')
      setTimeout(() => navigate('/login'), 3000)
    } catch (error) {
      setVerificationStatus('error')
      setError(error.response?.data?.detail || 'Verification failed')
      toast.error('Email verification failed')
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
              <p className="mt-2 text-gray-600">Redirecting to login...</p>
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
```

#### **2.2 Email Verification Status Component**
**File**: `src/components/auth/EmailVerificationStatus.jsx`
```jsx
import { useState } from 'react'
import { emailService } from '../../services/emailService'
import toast from 'react-hot-toast'

const EmailVerificationStatus = ({ user, onVerificationUpdate }) => {
  const [isResending, setIsResending] = useState(false)

  const handleResendVerification = async () => {
    setIsResending(true)
    try {
      await emailService.resendVerificationEmail(user.email)
      toast.success('Verification email sent!')
    } catch (error) {
      toast.error('Failed to send verification email')
    } finally {
      setIsResending(false)
    }
  }

  if (user.email_verified) {
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
```

### **Step 3: Password Reset Flow Implementation**

#### **3.1 Forgot Password Page**
**File**: `src/pages/ForgotPasswordPage.jsx`
```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { emailService } from '../services/emailService'
import toast from 'react-hot-toast'

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isEmailSent, setIsEmailSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      await emailService.requestPasswordReset(email)
      setIsEmailSent(true)
      toast.success('Password reset email sent!')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email')
    } finally {
      setIsLoading(false)
    }
  }

  if (isEmailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 p-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="mt-4 text-2xl font-bold text-gray-900">Check Your Email</h2>
            <p className="mt-2 text-gray-600">
              We've sent a password reset link to <strong>{email}</strong>
            </p>
            <p className="mt-4 text-sm text-gray-500">
              Didn't receive the email? Check your spam folder or{' '}
              <button 
                onClick={() => setIsEmailSent(false)}
                className="text-blue-600 hover:text-blue-500"
              >
                try again
              </button>
            </p>
            <Link 
              to="/login"
              className="mt-6 inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Forgot Password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </div>

          <div className="text-center">
            <Link 
              to="/login"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Back to Login
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ForgotPasswordPage
```

#### **3.2 Reset Password Page**
**File**: `src/pages/ResetPasswordPage.jsx`
```jsx
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

  useEffect(() => {
    if (token) {
      validateToken(token)
    }
  }, [token])

  const validateToken = async (resetToken) => {
    try {
      await emailService.validateResetToken(resetToken)
      setIsValidToken(true)
    } catch (error) {
      setIsValidToken(false)
      toast.error('Invalid or expired reset token')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }

    setIsLoading(true)
    
    try {
      await emailService.resetPassword(token, password)
      toast.success('Password reset successfully!')
      navigate('/login')
    } catch (error) {
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
            {password && <PasswordStrengthMeter password={password} />}
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
```

### **Step 4: User Notifications System**

#### **4.1 Notification Context**
**File**: `src/contexts/NotificationContext.jsx`
```jsx
import { createContext, useContext, useState, useEffect } from 'react'

const NotificationContext = createContext()

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now(),
      timestamp: new Date(),
      read: false,
      ...notification
    }
    setNotifications(prev => [newNotification, ...prev])
    setUnreadCount(prev => prev + 1)
  }

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    )
    setUnreadCount(0)
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
    setUnreadCount(prev => {
      const notification = notifications.find(n => n.id === id)
      return notification && !notification.read ? prev - 1 : prev
    })
  }

  // Simulate receiving security alerts (in real app, this would be via WebSocket/SSE)
  useEffect(() => {
    // Check for security alerts on mount
    // This would typically be replaced with WebSocket connection
  }, [])

  const value = {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}
```

#### **4.2 Notification Center Component**
**File**: `src/components/common/NotificationCenter.jsx`
```jsx
import { useState, useRef, useEffect } from 'react'
import { useNotifications } from '../../contexts/NotificationContext'

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'security':
        return (
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center h-8 w-8 rounded-full bg-red-100">
              <svg className="h-4 w-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
        )
      case 'email':
        return (
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100">
              <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        )
      default:
        return (
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center h-8 w-8 rounded-full bg-gray-100">
              <svg className="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        )
    }
  }

  const formatTimestamp = (timestamp) => {
    const now = new Date()
    const diff = now - new Date(timestamp)
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5-5v5zM4.828 4.828A4.95 4.95 0 016.75 4h10.5a4.95 4.95 0 011.922.828L22 2H2l2.828 2.828zM15 7H9v10h6V7z" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 flex items-center justify-center text-xs font-medium text-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  Mark all read
                </button>
              )}
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-200 hover:bg-gray-50 cursor-pointer ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex space-x-3">
                    {getNotificationIcon(notification.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {notification.title}
                      </p>
                      <p className="text-sm text-gray-500">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatTimestamp(notification.timestamp)}
                      </p>
                    </div>
                    {!notification.read && (
                      <div className="flex-shrink-0">
                        <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationCenter
```

### **Step 5: Route and Navigation Updates**

#### **5.1 Update AppRoutes**
**File**: `src/components/common/AppRoutes.jsx`
```jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from '../../pages/HomePage'
import LoginPage from '../../pages/LoginPage'
import RegisterPage from '../../pages/RegisterPage'
import DashboardPage from '../../pages/DashboardPage'
import VerifyEmailPage from '../../pages/VerifyEmailPage'
import ForgotPasswordPage from '../../pages/ForgotPasswordPage'
import ResetPasswordPage from '../../pages/ResetPasswordPage'
import ProtectedRoute from '../auth/ProtectedRoute'

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } 
      />
      {/* Redirect any unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
```

#### **5.2 Update App.jsx with Notification Provider**
**File**: `src/App.jsx`
```jsx
import { BrowserRouter as Router } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import AppRoutes from './components/common/AppRoutes'

function App() {
  return (
    <Router>
      <AuthProvider>
        <NotificationProvider>
          <div className="min-h-screen bg-gray-50">
            <AppRoutes />
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />
          </div>
        </NotificationProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
```

---

## 🔧 Integration Points

### **Environment Variables**
**File**: `.env`
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_EMAIL_FEATURES=true
```

### **Package Dependencies**
Add to `package.json`:
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "react-hot-toast": "^2.4.1"
  }
}
```

---

## 📋 Implementation Checklist

### **Phase 1: Email Verification** ✅
- [ ] Create `src/services/api.js`
- [ ] Create `src/services/emailService.js`
- [ ] Create `src/pages/VerifyEmailPage.jsx`
- [ ] Create `src/components/auth/EmailVerificationStatus.jsx`
- [ ] Update routes in `AppRoutes.jsx`
- [ ] Test email verification flow

### **Phase 2: Password Reset** ✅
- [ ] Create `src/pages/ForgotPasswordPage.jsx`
- [ ] Create `src/pages/ResetPasswordPage.jsx`
- [ ] Add password reset routes
- [ ] Update login page with "Forgot Password" link
- [ ] Test complete password reset flow

### **Phase 3: User Notifications** ✅
- [ ] Create `src/contexts/NotificationContext.jsx`
- [ ] Create `src/components/common/NotificationCenter.jsx`
- [ ] Create security alert components
- [ ] Update main layout with notification center
- [ ] Test notification system

### **Integration & Testing** ✅
- [ ] Update `App.jsx` with new providers
- [ ] Add environment variables
- [ ] Install required dependencies
- [ ] End-to-end testing of all email flows
- [ ] Mobile responsiveness testing
- [ ] Error handling validation

---

## 🚀 Expected Outcomes

After implementation, users will have:

1. **Complete Email Verification Flow**: Users receive emails, click links, get verified
2. **Self-Service Password Reset**: Users can reset passwords without admin intervention
3. **Real-time Security Alerts**: Users get notified of new device logins immediately
4. **Professional UI/UX**: Polished forms and flows matching your current design
5. **Error Handling**: Graceful handling of expired tokens, network issues, etc.

This plan provides a comprehensive roadmap for implementing all frontend email features that complement your completed backend system!
