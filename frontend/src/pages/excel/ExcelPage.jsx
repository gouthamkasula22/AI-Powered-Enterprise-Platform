/**
 * Excel Q&A Assistant Page
 * 
 * Main page for Excel file upload, analysis, and natural language queries.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ExcelUpload from '../../components/excel/ExcelUpload';
import DocumentList from '../../components/excel/DocumentList';
import { getUserDocuments } from '../../services/excel/excelService';

const ExcelPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getUserDocuments();
      setDocuments(response.documents);
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleUploadSuccess = (document) => {
    // Refresh document list
    loadDocuments();
    // Navigate to document detail page
    navigate(`/excel/${document.id}`);
  };

  const handleDocumentClick = (documentId) => {
    navigate(`/excel/${documentId}`);
  };

  const handleDocumentDelete = () => {
    // Refresh list after deletion
    loadDocuments();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Excel Q&A Assistant</h1>
          <p className="mt-2 text-gray-600">
            Upload Excel files and ask questions in natural language
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          <ExcelUpload onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Documents List */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Documents</h2>
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No documents yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload an Excel file to get started
              </p>
            </div>
          ) : (
            <DocumentList
              documents={documents}
              onDocumentClick={handleDocumentClick}
              onDocumentDelete={handleDocumentDelete}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ExcelPage;
