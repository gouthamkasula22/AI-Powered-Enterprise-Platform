// Authentication context will be implemented in Milestone 2
import { createContext, useContext, useState } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  // Placeholder functions - will be implemented in Milestone 2
  const login = async (email, password) => {
    console.log('Login function to be implemented')
  }

  const register = async (userData) => {
    console.log('Register function to be implemented')
  }

  const logout = () => {
    console.log('Logout function to be implemented')
  }

  const value = {
    user,
    isLoading,
    login,
    register,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
