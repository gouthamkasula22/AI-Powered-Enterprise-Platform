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
    console.log("API Error:", error.response?.status, error.response?.data);
    
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
      
      // Force logout
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      
      // Display message to user
      const message = error.response.data?.detail?.message || 
                     "Your session has expired or been revoked. Please login again.";
      
      // Redirect to login with message
      window.location.href = `/login?message=${encodeURIComponent(message)}`;
      return Promise.reject(error);
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
