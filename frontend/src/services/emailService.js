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

  async resetPassword(token, newPassword) {
    console.log('emailService.resetPassword called with:', { token, newPassword: '***' })
    const requestData = { 
      token, 
      new_password: newPassword 
    }
    console.log('Request data:', { ...requestData, new_password: '***' })
    
    const response = await apiClient.post('/api/v1/auth/reset-password', requestData)
    return response.data
  }
}
