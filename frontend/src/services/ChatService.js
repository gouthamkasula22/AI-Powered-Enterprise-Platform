import axios from 'axios';

// Create a config file later for environment-specific URLs
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // In production, relative to the domain
  : 'http://localhost:8000/api';  // In development, point to backend server

const API_ENDPOINTS = {
  THREADS: `${API_BASE_URL}/chat/threads`,
  MESSAGES: (threadId) => `${API_BASE_URL}/chat/threads/${threadId}/messages`,
  THREAD: (threadId) => `${API_BASE_URL}/chat/threads/${threadId}`,
};

class ChatService {
  static async getThreads() {
    try {
      const response = await axios.get(API_ENDPOINTS.THREADS);
      return response.data;
    } catch (error) {
      console.error('Error fetching chat threads:', error);
      throw error;
    }
  }
  
  static async getThread(threadId) {
    try {
      const response = await axios.get(API_ENDPOINTS.THREAD(threadId));
      return response.data;
    } catch (error) {
      console.error(`Error fetching thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async createThread(threadData) {
    try {
      const response = await axios.post(API_ENDPOINTS.THREADS, threadData);
      return response.data;
    } catch (error) {
      console.error('Error creating chat thread:', error);
      throw error;
    }
  }
  
  static async getMessages(threadId) {
    try {
      const response = await axios.get(API_ENDPOINTS.MESSAGES(threadId));
      return response.data;
    } catch (error) {
      console.error(`Error fetching messages for thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async sendMessage(threadId, messageData) {
    try {
      const response = await axios.post(API_ENDPOINTS.MESSAGES(threadId), messageData);
      return response.data;
    } catch (error) {
      console.error(`Error sending message to thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async getAIResponse(threadId) {
    try {
      // In a real implementation with streaming or SSE, this would be different
      // For now, we just fetch the latest AI message
      const response = await axios.get(API_ENDPOINTS.MESSAGES(threadId), {
        params: { 
          role: 'assistant',
          limit: 1,
          order: 'desc'
        }
      });
      
      return response.data[0];
    } catch (error) {
      console.error(`Error getting AI response for thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async deleteThread(threadId) {
    try {
      await axios.delete(API_ENDPOINTS.THREAD(threadId));
      return true;
    } catch (error) {
      console.error(`Error deleting thread ${threadId}:`, error);
      throw error;
    }
  }
}

export default ChatService;