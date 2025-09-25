import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const AuthContext = createContext()

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.headers.common['Content-Type'] = 'application/json'

// API version handling
const apiVersion = ''  // Remove v1 to match backend routes

// Request interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for token refresh and error handling
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // Handle auth errors (401 Unauthorized, 403 Forbidden with specific error codes)
    if (
      error.response && 
      (error.response.status === 401 || 
       (error.response.status === 403 && 
        (error.response.data?.detail?.error === "TOKEN_BLACKLISTED" || 
         error.response.data?.detail?.error === "USER_DEACTIVATED" ||
         error.response.data?.detail?.error === "TOKEN_INVALID")))
    ) {
      console.log("Session expired or revoked. Logging out...");
      
      // Get the error message
      const errorCode = error.response.data?.detail?.error || 'AUTHENTICATION_ERROR'
      const message = error.response.data?.detail?.message || 
                     "Your session has expired or been revoked. Please login again.";
      
      // Force logout
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      
      // Show user-friendly message
      if (errorCode === 'USER_DEACTIVATED') {
        toast.error('Your account has been deactivated by an administrator')
      } else if (errorCode === 'TOKEN_BLACKLISTED') {
        toast.error('Your session has been revoked by an administrator')
      } else {
        toast.error('Session expired. Please login again.')
      }
      
      // Redirect to login with appropriate message
      window.location.href = `/login?reason=${errorCode.toLowerCase()}&message=${encodeURIComponent(message)}`
      return Promise.reject(error)
    }
    return Promise.reject(error)
  }
)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  
  // Role-based access helpers
  const getUserRole = useCallback(() => {
    return user?.role || 'user'
  }, [user])
  
  const hasRole = useCallback((requiredRole) => {
    const userRole = getUserRole()
    const roleHierarchy = {
      'user': 1,
      'admin': 2,
      'superadmin': 3,
      // Support legacy uppercase roles for backward compatibility
      'USER': 1,
      'ADMIN': 2,
      'SUPERADMIN': 3
    }
    
    return (roleHierarchy[userRole] || 0) >= (roleHierarchy[requiredRole] || 0)
  }, [getUserRole])
  
  const hasPermission = useCallback((permission) => {
    const userRole = getUserRole()
    const rolePermissions = {
      'user': ['read_own_profile'],
      'admin': ['read_own_profile', 'read_users', 'manage_users'],
      'superadmin': ['read_own_profile', 'read_users', 'manage_users', 'manage_admins', 'system_admin'],
      // Support legacy uppercase roles for backward compatibility
      'USER': ['read_own_profile'],
      'ADMIN': ['read_own_profile', 'read_users', 'manage_users'],
      'SUPERADMIN': ['read_own_profile', 'read_users', 'manage_users', 'manage_admins', 'system_admin']
    }
    
    return rolePermissions[userRole]?.includes(permission) || false
  }, [getUserRole])
  
  const isAdmin = useCallback(() => {
    return hasRole('ADMIN')
  }, [hasRole])
  
  const isSuperAdmin = useCallback(() => {
    return hasRole('SUPERADMIN')
  }, [hasRole])

  // Check if user is logged in on app start
  useEffect(() => {
    const initializeAuth = () => {
      const token = localStorage.getItem('access_token')
      const userData = localStorage.getItem('user')
      
      if (token && userData) {
        try {
          const parsedUser = JSON.parse(userData)
          setUser(parsedUser)
          setIsAuthenticated(true)
          
          // Validate token immediately to check if it's still valid
          validateToken()
        } catch (error) {
          console.error('Error parsing user data:', error)
          logout()
        }
      }
      setIsLoading(false)
    }

    initializeAuth()
    
    // Set up periodic token validation every 5 minutes
    const tokenValidationInterval = setInterval(() => {
      validateToken()
    }, 5 * 60 * 1000) // 5 minutes
    
    return () => {
      clearInterval(tokenValidationInterval)
    }
  }, [])
  
  // Validate token to check if it's still valid or has been blacklisted
  const validateToken = async () => {
    const token = localStorage.getItem('access_token')
    if (!token || !isAuthenticated) return
    
    try {
      // Call the dedicated token validation endpoint
      await axios.get('/api/auth/validate-token')
      console.log('Token validation successful')
    } catch (error) {
      // If we get a specific error code, handle it directly here
      if (error.response?.status === 403 && 
          (error.response?.data?.detail?.error === "USER_DEACTIVATED" || 
           error.response?.data?.detail?.error === "TOKEN_BLACKLISTED")) {
        
        // Get the error message
        const message = error.response?.data?.detail?.message || 
                       "Your session has been revoked. Please login again.";
                       
        // Force logout
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        setUser(null)
        setIsAuthenticated(false)
        
        // Show notification
        toast.error(message)
        
        // Redirect to login
        window.location.href = `/login?message=${encodeURIComponent(message)}`
      }
      // Other errors will be handled by the axios interceptor
      console.error('Token validation failed:', error)
    }
  }

  const login = async (emailOrData, password, showToast = true) => {
    try {
      setIsLoading(true)
      
      // Handle OAuth login data format
      if (typeof emailOrData === 'object' && emailOrData.user && emailOrData.tokens) {
        const { user: userData, tokens } = emailOrData
        
        // Store tokens and user data for OAuth login
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
        localStorage.setItem('user', JSON.stringify(userData))
        
        setUser(userData)
        setIsAuthenticated(true)
        
        return { success: true }
      }
      
      // Handle regular email/password login
      const response = await axios.post('/api/auth/login', {
        email: emailOrData,
        password
      })

      const { user: userData, access_token, refresh_token } = response.data
      
      // Store tokens and user data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setUser(userData)
      setIsAuthenticated(true)
      
      if (showToast) {
        toast.success('Login successful')
      }
      return { success: true }
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (userData) => {
    try {
      setIsLoading(true)
      
      const response = await axios.post('/api/auth/register', {
        email: userData.email,
        password: userData.password
      })

      toast.success('Registration successful! Please check your email for verification.')
      return { success: true, data: response.data }
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
    setIsAuthenticated(false)
    toast.success('Logged out successfully')
  }

  const verifyEmail = useCallback(async (token) => {
    try {
      setIsLoading(true)
      
      const response = await axios.post('/api/auth/verify-email', {
        token
      })
      
      // Update user data to reflect email verification
      if (user) {
        const updatedUser = { ...user, is_verified: true }
        setUser(updatedUser)
        localStorage.setItem('user', JSON.stringify(updatedUser))
      }
      
      toast.success('Email verified successfully')
      return { success: true, data: response.data }
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Email verification failed'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setIsLoading(false)
    }
  }, [user])

  const refreshUserData = useCallback(async () => {
    try {
      const response = await axios.get('/api/users/me')
      const userData = response.data
      
      // Extract user data from the response (API returns {user: UserResponse})
      const user = userData.user || userData
      console.log('refreshUserData - received:', userData)
      console.log('refreshUserData - setting user to:', user)
      
      setUser(user)
      localStorage.setItem('user', JSON.stringify(user))
      
      return { success: true, data: user }
    } catch (error) {
      console.error('Failed to refresh user data:', error)
      return { success: false, error: error.response?.data?.detail || 'Failed to refresh user data' }
    }
  }, [])

  const resendVerification = async (email) => {
    try {
      setIsLoading(true)
      
      const response = await axios.post('/api/auth/resend-verification', {
        email
      })
      
      toast.success('Verification email sent')
      return { success: true, data: response.data }
      
    } catch (error) {
      console.error('Resend verification error:', error.response?.data)
      const message = error.response?.data?.detail || 'Failed to send verification email'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setIsLoading(false)
    }
  }

  const updateProfile = async (profileData) => {
    setIsLoading(true)
    try {
      console.log('Updating profile with data:', profileData)
      const response = await axios.put('/api/auth/profile', profileData)
      
      // Profile update returns UserResponse directly (not wrapped in { user: ... })
      const updatedUser = response.data
      console.log('Profile update response:', updatedUser)
      console.log('Setting user state to:', updatedUser)
      setUser(updatedUser)
      localStorage.setItem('user', JSON.stringify(updatedUser))
      
      return { success: true, user: updatedUser }
      
    } catch (error) {
      console.error('Profile update error:', error.response?.data)
      const message = error.response?.data?.detail || 'Failed to update profile'
      return { success: false, error: message }
    } finally {
      setIsLoading(false)
    }
  }
  
  // Helper function to get authorization headers for API requests
  const getAuthHeader = () => {
    const token = localStorage.getItem('access_token')
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    verifyEmail,
    resendVerification,
    refreshUserData,
    updateProfile,
    // Role-based access control
    getUserRole,
    hasRole,
    hasPermission,
    isAdmin,
    isSuperAdmin,
    getAuthHeader
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
