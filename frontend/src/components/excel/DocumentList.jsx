/**
 * Document List Component
 * 
 * Displays a list of uploaded Excel documents with status and actions.
 */

import React, { useState } from 'react';
import { deleteDocument } from '../../services/excel/excelService';

const DocumentList = ({ documents, onDocumentClick, onDocumentDelete }) => {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (e, documentId) => {
    e.stopPropagation(); // Prevent triggering document click

    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      setDeletingId(documentId);
      await deleteDocument(documentId);
      onDocumentDelete();
    } catch (err) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      ready: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      uploaded: 'bg-blue-100 text-blue-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.uploaded}`}>
        {status === 'processing' && (
          <svg className="animate-spin -ml-0.5 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="bg-white shadow overflow-hidden rounded-lg">
      <ul className="divide-y divide-gray-200">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="hover:bg-gray-50 cursor-pointer transition-colors"
            onClick={() => onDocumentClick(doc.id)}
          >
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  {/* Document Name and Status */}
                  <div className="flex items-center space-x-3">
                    <svg
                      className="h-8 w-8 text-green-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {doc.original_filename}
                      </p>
                      <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>•</span>
                        <span>{doc.sheet_count} sheet{doc.sheet_count !== 1 ? 's' : ''}</span>
                        <span>•</span>
                        <span>{doc.total_rows.toLocaleString()} rows</span>
                      </div>
                    </div>
                  </div>

                  {/* Upload Date */}
                  <div className="mt-2 text-xs text-gray-500">
                    Uploaded {formatDate(doc.uploaded_at)}
                  </div>
                </div>

                {/* Status and Actions */}
                <div className="ml-4 flex items-center space-x-3">
                  {getStatusBadge(doc.status)}
                  
                  <button
                    onClick={(e) => handleDelete(e, doc.id)}
                    disabled={deletingId === doc.id}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete document"
                  >
                    {deletingId === doc.id ? (
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    )}
                  </button>

                  <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              </div>

              {/* Error Message */}
              {doc.status === 'error' && doc.error_message && (
                <div className="mt-2 text-sm text-red-600">
                  Error: {doc.error_message}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DocumentList;
