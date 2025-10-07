/**
 * Query History Component
 * 
 * Displays the history of submitted queries with their results.
 */

import React, { useState } from 'react';
import ResultVisualization from './ResultVisualization';

const QueryHistory = ({ queries, onRefresh }) => {
  const [expandedQueries, setExpandedQueries] = useState(new Set());

  const toggleExpanded = (queryId) => {
    const newExpanded = new Set(expandedQueries);
    if (newExpanded.has(queryId)) {
      newExpanded.delete(queryId);
    } else {
      newExpanded.add(queryId);
    }
    setExpandedQueries(newExpanded);
  };

  if (!queries || queries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Query History</h2>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Refresh
            </button>
          )}
        </div>
        <p className="text-gray-500 text-center py-4">No queries yet</p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
    };

    const displayStatus = status === 'success' ? 'completed' : status;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {displayStatus.charAt(0).toUpperCase() + displayStatus.slice(1)}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Query History</h2>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          )}
        </div>
        
        <div className="space-y-3">
          {queries.map((query) => {
            const isExpanded = expandedQueries.has(query.id);
            const hasResult = query.result || query.generated_code;

            return (
              <div
                key={query.id}
                className="border rounded-lg overflow-hidden"
              >
                {/* Query Header */}
                <div
                  className={`p-4 ${hasResult ? 'cursor-pointer hover:bg-gray-50' : 'bg-white'} transition-colors`}
                  onClick={() => hasResult && toggleExpanded(query.id)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{query.query_text}</p>
                      {query.sheet_name && (
                        <p className="text-xs text-gray-500 mt-1">Sheet: {query.sheet_name}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(query.status)}
                      {hasResult && (
                        <svg
                          className={`h-5 w-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center text-xs text-gray-500">
                    <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {new Date(query.created_at).toLocaleString()}
                  </div>

                  {query.error_message && !isExpanded && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 rounded p-2">
                      {query.error_message}
                    </div>
                  )}
                </div>

                {/* Expanded Content */}
                {isExpanded && hasResult && (
                  <div className="border-t bg-gray-50 p-4 space-y-4">
                    {/* Generated Code */}
                    {query.generated_code && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                          </svg>
                          Generated Code
                        </h4>
                        <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-xs overflow-x-auto">
                          <code>{query.generated_code}</code>
                        </pre>
                      </div>
                    )}

                    {/* Execution Result */}
                    {query.result && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Result
                        </h4>
                        <ResultVisualization 
                          result={query.result}
                          executionTime={query.execution_time_ms}
                        />
                      </div>
                    )}

                    {/* Error Message */}
                    {query.error_message && (
                      <div>
                        <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center">
                          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Error
                        </h4>
                        <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
                          {query.error_message}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default QueryHistory;
