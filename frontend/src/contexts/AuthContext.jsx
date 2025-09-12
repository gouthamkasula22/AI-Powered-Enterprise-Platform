import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const AuthContext = createContext()

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.headers.common['Content-Type'] = 'application/json'

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
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
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
        } catch (error) {
          console.error('Error parsing user data:', error)
          logout()
        }
      }
      setIsLoading(false)
    }

    initializeAuth()
  }, [])

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
      const response = await axios.post('/api/v1/auth/login', {
        email: emailOrData,
        password
      })

      const { user: userData, tokens } = response.data
      
      // Store tokens and user data
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
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
      
      const response = await axios.post('/api/v1/auth/register', {
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
      
      const response = await axios.post('/api/v1/auth/verify-email', {
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
      const response = await axios.get('/api/v1/auth/me')
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
      
      const response = await axios.post('/api/v1/auth/resend-verification', {
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
      const response = await axios.put('/api/v1/auth/profile', profileData)
      
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
    updateProfile
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
