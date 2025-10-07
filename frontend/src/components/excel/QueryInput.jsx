/**
 * Query Input Component
 * 
 * Natural language query input with submission handling.
 */

import React, { useState, useEffect } from 'react';
import { getExampleQuestions } from '../../services/excel/excelService';

const QueryInput = ({ onSubmit, disabled, documentId, sheetName }) => {
  const [queryText, setQueryText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [exampleQueries, setExampleQueries] = useState([
    'What columns are available?',
    'Show me the top 10 rows',
    'What is the average of numeric columns?',
    'How many rows are there?',
  ]);

  // Fetch example questions when document is loaded
  useEffect(() => {
    const fetchExamples = async () => {
      if (documentId && !disabled) {
        try {
          const data = await getExampleQuestions(documentId, sheetName);
          if (data?.questions && data.questions.length > 0) {
            setExampleQueries(data.questions);
          }
        } catch (err) {
          console.error('Failed to fetch example questions:', err);
          // Keep default examples if fetch fails
        }
      }
    };

    fetchExamples();
  }, [documentId, sheetName, disabled]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!queryText.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit(queryText.trim());
      setQueryText(''); // Clear input on success
    } catch (err) {
      console.error('Query submission error:', err);
      setError(err.response?.data?.detail || 'Failed to submit query. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExampleClick = (example) => {
    setQueryText(example);
  };

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Ask a Question</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Type your question in natural language..."
            disabled={disabled || submitting}
            rows={4}
            className={`
              w-full px-3 py-2 border rounded-lg resize-none
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              ${error ? 'border-red-300' : 'border-gray-300'}
            `}
          />
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled || submitting || !queryText.trim()}
          className={`
            w-full px-4 py-2 rounded-lg font-medium transition-colors
            ${
              disabled || submitting || !queryText.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }
          `}
        >
          {submitting ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Submitting...
            </span>
          ) : (
            'Ask Question'
          )}
        </button>
      </form>

      {/* Example Queries */}
      <div className="mt-6">
        <p className="text-sm font-medium text-gray-700 mb-2">Example questions:</p>
        <div className="space-y-2">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={disabled || submitting}
              className={`
                w-full text-left px-3 py-2 text-sm rounded-lg border border-gray-200
                transition-colors
                ${
                  disabled || submitting
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:bg-gray-50 hover:border-blue-300'
                }
              `}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {disabled && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Document is still processing. Please wait until it's ready.
          </p>
        </div>
      )}
    </div>
  );
};

export default QueryInput;
