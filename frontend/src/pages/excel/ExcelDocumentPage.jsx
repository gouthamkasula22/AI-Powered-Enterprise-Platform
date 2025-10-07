/**
 * Excel Document Detail Page
 * 
 * View document details, sheets, and submit natural language queries.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getDocument,
  getDocumentSheets,
  getSheetPreview,
  submitQuery,
  getQueryHistory,
  executeQuery,
} from '../../services/excel/excelService';
import SheetSelector from '../../components/excel/SheetSelector';
import DataPreview from '../../components/excel/DataPreview';
import QueryInput from '../../components/excel/QueryInput';
import QueryHistory from '../../components/excel/QueryHistory';

const ExcelDocumentPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [sheets, setSheets] = useState([]);
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const queryHistoryRef = useRef(null);

  useEffect(() => {
    loadDocumentData();
  }, [id]);

  useEffect(() => {
    if (selectedSheet) {
      loadSheetPreview(selectedSheet.sheet_name);
    }
  }, [selectedSheet]);

  const loadDocumentData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [docData, sheetsData, queriesData] = await Promise.all([
        getDocument(id),
        getDocumentSheets(id),
        getQueryHistory(id),
      ]);

      setDocument(docData);
      setSheets(sheetsData);
      setQueries(queriesData);

      // Select first sheet by default
      if (sheetsData.length > 0) {
        setSelectedSheet(sheetsData[0]);
      }
    } catch (err) {
      console.error('Error loading document:', err);
      setError('Failed to load document. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadSheetPreview = async (sheetName) => {
    try {
      const preview = await getSheetPreview(id, sheetName, 20);
      setPreviewData(preview);
    } catch (err) {
      console.error('Error loading preview:', err);
      setError('Failed to load sheet preview.');
    }
  };

  const handleSheetChange = (sheet) => {
    setSelectedSheet(sheet);
  };

  const handleQuerySubmit = async (queryText) => {
    try {
      // Submit the query
      const query = await submitQuery(id, queryText, selectedSheet?.sheet_name);
      
      // Add to queries list
      setQueries([query, ...queries]);
      
      // Execute the query
      const result = await executeQuery(id, query.id);
      
      // Update the query with execution result
      const updatedQuery = {
        ...query,
        status: result.status,
        generated_code: result.generated_code,
        execution_result: result.execution_result,
        execution_time_ms: result.execution_time_ms,
        error_message: result.error_message,
      };
      
      // Update queries list with executed query
      setQueries([updatedQuery, ...queries]);
      
      // Scroll to query history
      setTimeout(() => {
        queryHistoryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 100);
      
      return updatedQuery;
    } catch (err) {
      console.error('Error submitting query:', err);
      throw err;
    }
  };

  const handleQueryRefresh = async () => {
    try {
      const queriesData = await getQueryHistory(id);
      setQueries(queriesData);
    } catch (err) {
      console.error('Error refreshing queries:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Document not found'}</p>
          <button
            onClick={() => navigate('/excel')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/excel')}
            className="text-blue-600 hover:text-blue-800 font-medium mb-4 flex items-center"
          >
            <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Documents
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{document.original_filename}</h1>
              <p className="mt-1 text-sm text-gray-600">
                {document.sheet_count} sheet{document.sheet_count !== 1 ? 's' : ''} • {' '}
                {document.total_rows.toLocaleString()} rows • {' '}
                {document.total_columns} columns
              </p>
            </div>
            
            <span
              className={`
                inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                ${document.status === 'ready' ? 'bg-green-100 text-green-800' : ''}
                ${document.status === 'processing' ? 'bg-yellow-100 text-yellow-800' : ''}
                ${document.status === 'error' ? 'bg-red-100 text-red-800' : ''}
              `}
            >
              {document.status.charAt(0).toUpperCase() + document.status.slice(1)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Sheets and Preview */}
          <div className="lg:col-span-2 space-y-6">
            {/* Sheet Selector */}
            <SheetSelector
              sheets={sheets}
              selectedSheet={selectedSheet}
              onSheetChange={handleSheetChange}
            />

            {/* Data Preview */}
            {previewData && (
              <DataPreview
                data={previewData}
                selectedSheet={selectedSheet}
              />
            )}
          </div>

          {/* Right Column - Query Interface */}
          <div className="space-y-6">
            {/* Query Input */}
            <QueryInput
              onSubmit={handleQuerySubmit}
              disabled={document.status !== 'ready'}
              documentId={parseInt(id)}
              sheetName={selectedSheet?.sheet_name}
            />

            {/* Query History */}
            <div ref={queryHistoryRef}>
              <QueryHistory 
                queries={queries}
                onRefresh={handleQueryRefresh}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExcelDocumentPage;
