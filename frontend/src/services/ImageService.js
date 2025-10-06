import apiClient from './api.js';

const IMAGE_API_BASE = '/api/images';

export const imageService = {
  // Generate a new image
  async generateImage(params) {
    const response = await apiClient.post(`${IMAGE_API_BASE}/generate`, params);
    return response.data;
  },

  // Get task status and progress
  async getTaskStatus(taskId) {
    const response = await apiClient.get(`${IMAGE_API_BASE}/tasks/${taskId}/status`);
    return response.data;
  },

  // Get user's image gallery
  async getUserGallery(page = 1, limit = 20) {
    const response = await apiClient.get(`${IMAGE_API_BASE}/gallery?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Get images for a specific thread
  async getThreadImages(threadId, page = 1, limit = 20) {
    const response = await apiClient.get(`${IMAGE_API_BASE}/thread/${threadId}?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Get specific image details
  async getImage(imageId) {
    const response = await apiClient.get(`${IMAGE_API_BASE}/${imageId}`);
    return response.data;
  },

  // Download image as file
  async downloadImage(imageId, filename = null) {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}${IMAGE_API_BASE}/${imageId}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `image-${imageId}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  // Delete an image
  async deleteImage(imageId) {
    const response = await apiClient.delete(`${IMAGE_API_BASE}/${imageId}`);
    return response.data;
  },

  // Update image metadata
  async updateImage(imageId, updates) {
    const response = await apiClient.put(`${IMAGE_API_BASE}/${imageId}`, updates);
    return response.data;
  },

  // Create gallery collection
  async createCollection(name, description = '') {
    const response = await apiClient.post(`${IMAGE_API_BASE}/collections`, { name, description });
    return response.data;
  },

  // Get user's collections
  async getCollections() {
    const response = await apiClient.get(`${IMAGE_API_BASE}/collections`);
    return response.data;
  },

  // Add image to collection
  async addToCollection(collectionId, imageId) {
    const response = await apiClient.post(`${IMAGE_API_BASE}/collections/${collectionId}/images`, { image_id: imageId });
    return response.data;
  },

  // Remove image from collection
  async removeFromCollection(collectionId, imageId) {
    const response = await apiClient.delete(`${IMAGE_API_BASE}/collections/${collectionId}/images/${imageId}`);
    return response.data;
  },

  // Get generation statistics
  async getGenerationStats() {
    const response = await apiClient.get(`${IMAGE_API_BASE}/stats`);
    return response.data;
  }
};

// Export individual functions for easier imports
export const {
  generateImage,
  getTaskStatus,
  getUserGallery,
  getThreadImages,
  getImage,
  downloadImage,
  deleteImage,
  updateImage,
  createCollection,
  getCollections,
  addToCollection,
  removeFromCollection,
  getGenerationStats
} = imageService;

export default imageService;