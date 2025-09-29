import React, { useEffect } from 'react'
import toast from 'react-hot-toast'
import { useAuth } from '../../contexts/AuthContext'

/**
 * Professional error handling system for role-based operations
 * Provides centralized error management with user-friendly messages
 */

// Error types and their corresponding user-friendly messages
const ERROR_MESSAGES = {
  // Authentication errors
  AUTHENTICATION_REQUIRED: 'Please log in to access this feature.',
  INVALID_CREDENTIALS: 'Invalid email or password. Please try again.',
  TOKEN_EXPIRED: 'Your session has expired. Please log in again.',
  TOKEN_INVALID: 'Invalid authentication token. Please log in again.',
  
  // Authorization errors
  INSUFFICIENT_PERMISSIONS: 'You don\'t have permission to perform this action.',
  ROLE_REQUIRED: 'This feature requires a higher access level.',
  ADMIN_REQUIRED: 'Administrator privileges are required for this action.',
  SUPERADMIN_REQUIRED: 'Super administrator privileges are required for this action.',
  
  // User management errors
  USER_NOT_FOUND: 'The requested user could not be found.',
  USER_ALREADY_EXISTS: 'A user with this email already exists.',
  INVALID_USER_DATA: 'The provided user information is invalid.',
  EMAIL_NOT_VERIFIED: 'Please verify your email address before proceeding.',
  
  // System errors
  SERVER_ERROR: 'A server error occurred. Please try again later.',
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
  
  // Validation errors
  VALIDATION_ERROR: 'Please check your input and try again.',
  REQUIRED_FIELD_MISSING: 'Please fill in all required fields.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  PASSWORD_TOO_WEAK: 'Password must meet security requirements.',
  
  // Role-based feature errors
  FEATURE_NOT_AVAILABLE: 'This feature is not available for your account type.',
  UPGRADE_REQUIRED: 'Please contact an administrator to access this feature.'
}

// Error severity levels
const ERROR_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
}

/**
 * Parse error response and extract meaningful information
 */
export const parseError = (error) => {
  // Handle axios errors
  if (error.response) {
    const status = error.response.status
    const data = error.response.data
    
    switch (status) {
      case 401:
        return {
          type: 'AUTHENTICATION_REQUIRED',
          message: data?.detail || ERROR_MESSAGES.AUTHENTICATION_REQUIRED,
          severity: ERROR_SEVERITY.HIGH
        }
      case 403:
        return {
          type: 'INSUFFICIENT_PERMISSIONS',
          message: data?.detail || ERROR_MESSAGES.INSUFFICIENT_PERMISSIONS,
          severity: ERROR_SEVERITY.MEDIUM
        }
      case 404:
        return {
          type: 'USER_NOT_FOUND',
          message: data?.detail || ERROR_MESSAGES.USER_NOT_FOUND,
          severity: ERROR_SEVERITY.LOW
        }
      case 422:
        return {
          type: 'VALIDATION_ERROR',
          message: data?.detail || ERROR_MESSAGES.VALIDATION_ERROR,
          severity: ERROR_SEVERITY.LOW,
          details: data?.errors
        }
      case 500:
        return {
          type: 'SERVER_ERROR',
          message: ERROR_MESSAGES.SERVER_ERROR,
          severity: ERROR_SEVERITY.CRITICAL
        }
      default:
        return {
          type: 'UNKNOWN_ERROR',
          message: data?.detail || ERROR_MESSAGES.UNKNOWN_ERROR,
          severity: ERROR_SEVERITY.MEDIUM
        }
    }
  }
  
  // Handle network errors
  if (error.request) {
    return {
      type: 'NETWORK_ERROR',
      message: ERROR_MESSAGES.NETWORK_ERROR,
      severity: ERROR_SEVERITY.HIGH
    }
  }
  
  // Handle other errors
  return {
    type: 'UNKNOWN_ERROR',
    message: error.message || ERROR_MESSAGES.UNKNOWN_ERROR,
    severity: ERROR_SEVERITY.MEDIUM
  }
}

/**
 * Display error message with appropriate styling and actions
 */
export const displayError = (error, options = {}) => {
  const parsedError = typeof error === 'string' ? { message: error, severity: ERROR_SEVERITY.LOW } : parseError(error)
  const { showToast = true, duration = 5000 } = options
  
  if (showToast) {
    const toastOptions = {
      duration,
      style: {
        background: '#FEF2F2',
        color: '#B91C1C',
        border: '1px solid #FCA5A5'
      }
    }
    
    // Add action button for certain errors
    if (parsedError.type === 'AUTHENTICATION_REQUIRED') {
      toast.error(parsedError.message, {
        ...toastOptions,
        action: {
          label: 'Login',
          onClick: () => window.location.href = '/login'
        }
      })
    } else {
      toast.error(parsedError.message, toastOptions)
    }
  }
  
  return parsedError
}

/**
 * Role-based error handler component
 */
export const RoleErrorHandler = ({ children, fallback = null }) => {
  const { isAuthenticated, getUserRole } = useAuth()
  
  const handleRoleError = (error) => {
    const parsedError = parseError(error)
    
    // Provide role-specific error messages
    if (parsedError.type === 'INSUFFICIENT_PERMISSIONS') {
      const userRole = getUserRole()
      let specificMessage = ERROR_MESSAGES.INSUFFICIENT_PERMISSIONS
      
      if (['USER', 'user'].includes(userRole)) {
        specificMessage = 'This feature requires administrator access. Please contact your system administrator.'
      } else if (['ADMIN', 'admin'].includes(userRole)) {
        specificMessage = 'This feature requires super administrator access.'
      }
      
      displayError({ ...parsedError, message: specificMessage })
    } else {
      displayError(error)
    }
  }
  
  // Provide error handler to children
  if (typeof children === 'function') {
    return children({ handleError: handleRoleError })
  }
  
  return children
}

/**
 * Error boundary component for role-based operations
 */
export class RoleErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Role-based operation error:', error, errorInfo)
    displayError(error)
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Something went wrong</h3>
              <p className="mt-2 text-sm text-gray-500">
                An error occurred while processing your request. Please try again.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      )
    }
    
    return this.props.children
  }
}

/**
 * Hook for handling errors in role-based operations
 */
export const useRoleErrorHandler = () => {
  const { getUserRole, isAuthenticated } = useAuth()
  
  const handleError = (error, context = {}) => {
    const parsedError = parseError(error)
    
    // Add role context to error
    const enrichedError = {
      ...parsedError,
      context: {
        userRole: getUserRole(),
        isAuthenticated,
        ...context
      }
    }
    
    // Log error for debugging
    console.error('Role-based operation failed:', enrichedError)
    
    // Display user-friendly error
    displayError(enrichedError)
    
    return enrichedError
  }
  
  const handleAsyncError = async (asyncOperation, context = {}) => {
    try {
      return await asyncOperation()
    } catch (error) {
      return handleError(error, context)
    }
  }
  
  return {
    handleError,
    handleAsyncError,
    displayError,
    parseError
  }
}

export default {
  parseError,
  displayError,
  RoleErrorHandler,
  RoleErrorBoundary,
  useRoleErrorHandler,
  ERROR_MESSAGES,
  ERROR_SEVERITY
}