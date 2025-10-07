/**
 * Excel API Service
 * 
 * Handles all Excel-related API calls.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const EXCEL_API_URL = `${API_BASE_URL}/api/v1/excel`;

/**
 * Get authentication headers with JWT token
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Authorization': `Bearer ${token}`,
  };
};

/**
 * Upload an Excel file
 */
export const uploadExcelFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${EXCEL_API_URL}/upload`, formData, {
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Get all documents for current user
 */
export const getUserDocuments = async (skip = 0, limit = 50) => {
  const response = await axios.get(`${EXCEL_API_URL}/documents`, {
    headers: getAuthHeaders(),
    params: { skip, limit },
  });

  return response.data;
};

/**
 * Get document details by ID
 */
export const getDocument = async (documentId) => {
  const response = await axios.get(`${EXCEL_API_URL}/${documentId}`, {
    headers: getAuthHeaders(),
  });

  return response.data;
};

/**
 * Get all sheets for a document
 */
export const getDocumentSheets = async (documentId) => {
  const response = await axios.get(`${EXCEL_API_URL}/${documentId}/sheets`, {
    headers: getAuthHeaders(),
  });

  return response.data;
};

/**
 * Get sheet preview data
 */
export const getSheetPreview = async (documentId, sheetName, rows = 10) => {
  const response = await axios.get(
    `${EXCEL_API_URL}/${documentId}/sheets/${encodeURIComponent(sheetName)}/preview`,
    {
      headers: getAuthHeaders(),
      params: { rows },
    }
  );

  return response.data;
};

/**
 * Delete a document
 */
export const deleteDocument = async (documentId) => {
  await axios.delete(`${EXCEL_API_URL}/${documentId}`, {
    headers: getAuthHeaders(),
  });
};

/**
 * Submit a natural language query
 */
export const submitQuery = async (documentId, queryText, targetSheet = null) => {
  const response = await axios.post(
    `${EXCEL_API_URL}/${documentId}/query`,
    {
      query_text: queryText,
      target_sheet: targetSheet,
    },
    {
      headers: getAuthHeaders(),
    }
  );

  return response.data;
};

/**
 * Execute a saved query
 */
export const executeQuery = async (documentId, queryId) => {
  const response = await axios.post(
    `${EXCEL_API_URL}/${documentId}/queries/${queryId}/execute`,
    {},
    {
      headers: getAuthHeaders(),
    }
  );

  return response.data;
};

/**
 * Get query history for a document
 */
export const getQueryHistory = async (documentId, limit = 20) => {
  const response = await axios.get(`${EXCEL_API_URL}/${documentId}/queries`, {
    headers: getAuthHeaders(),
    params: { limit },
  });

  return response.data;
};

/**
 * Get intelligent example questions based on document columns
 */
export const getExampleQuestions = async (documentId, sheetName = null) => {
  const response = await axios.get(`${EXCEL_API_URL}/${documentId}/example-questions`, {
    headers: getAuthHeaders(),
    params: sheetName ? { sheet_name: sheetName } : {},
  });

  return response.data;
};

/**
 * Get cache statistics
 */
export const getCacheStats = async () => {
  const response = await axios.get(`${EXCEL_API_URL}/cache/stats`, {
    headers: getAuthHeaders(),
  });

  return response.data;
};

/**
 * Clear cache
 */
export const clearCache = async () => {
  await axios.post(`${EXCEL_API_URL}/cache/clear`, {}, {
    headers: getAuthHeaders(),
  });
};

/**
 * Get optimizer metrics
 */
export const getOptimizerMetrics = async () => {
  const response = await axios.get(`${EXCEL_API_URL}/optimizer/metrics`, {
    headers: getAuthHeaders(),
  });

  return response.data;
};

/**
 * Clear query cache
 */
export const clearQueryCache = async () => {
  await axios.post(`${EXCEL_API_URL}/optimizer/cache/clear`, {}, {
    headers: getAuthHeaders(),
  });
};

export default {
  uploadExcelFile,
  getUserDocuments,
  getDocument,
  getDocumentSheets,
  getSheetPreview,
  deleteDocument,
  submitQuery,
  executeQuery,
  getQueryHistory,
  getCacheStats,
  clearCache,
  getOptimizerMetrics,
  clearQueryCache,
};
