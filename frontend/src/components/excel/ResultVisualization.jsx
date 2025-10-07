/**
 * Result Visualization Component
 * 
 * Displays query execution results in various formats:
 * - Scalar values (numbers, strings, booleans)
 * - DataFrames (tables)
 * - Series (lists)
 * - Arrays (lists)
 */

import React, { useState } from 'react';

const ResultVisualization = ({ result, executionTime }) => {
  const [showFullData, setShowFullData] = useState(false);

  if (!result) {
    return null;
  }

  // Handle different result types
  const renderResult = () => {
    // Scalar values (number, string, boolean, null)
    if (typeof result === 'number' || typeof result === 'string' || 
        typeof result === 'boolean' || result === null) {
      return (
        <div className="bg-gray-50 rounded-lg p-6 text-center">
          <div className="text-sm text-gray-500 mb-2">Result</div>
          <div className="text-3xl font-bold text-gray-900">
            {result === null ? 'null' : result.toString()}
          </div>
          {typeof result === 'number' && (
            <div className="text-sm text-gray-500 mt-1">
              {result.toLocaleString()}
            </div>
          )}
        </div>
      );
    }

    // DataFrame (object with data and columns)
    if (result.data && result.columns) {
      return renderDataFrame(result);
    }

    // Series or Array
    if (Array.isArray(result)) {
      return renderArray(result);
    }

    // Generic object
    if (typeof result === 'object') {
      return renderObject(result);
    }

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    );
  };

  const renderDataFrame = (df) => {
    const { data, columns, index } = df;
    const maxRows = showFullData ? data.length : Math.min(10, data.length);
    const displayData = data.slice(0, maxRows);

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>{data.length} rows × {columns.length} columns</span>
          {data.length > 10 && (
            <button
              onClick={() => setShowFullData(!showFullData)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              {showFullData ? 'Show less' : `Show all ${data.length} rows`}
            </button>
          )}
        </div>

        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {index && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Index
                  </th>
                )}
                {columns.map((col, idx) => (
                  <th
                    key={idx}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayData.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-gray-50">
                  {index && (
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                      {index[rowIdx]}
                    </td>
                  )}
                  {columns.map((col, colIdx) => (
                    <td key={colIdx} className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                      {formatCellValue(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!showFullData && data.length > 10 && (
          <div className="text-center text-sm text-gray-500">
            Showing first 10 of {data.length} rows
          </div>
        )}
      </div>
    );
  };

  const renderArray = (arr) => {
    const maxItems = showFullData ? arr.length : Math.min(20, arr.length);
    const displayItems = arr.slice(0, maxItems);

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>{arr.length} items</span>
          {arr.length > 20 && (
            <button
              onClick={() => setShowFullData(!showFullData)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              {showFullData ? 'Show less' : `Show all ${arr.length} items`}
            </button>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-4 space-y-1">
          {displayItems.map((item, idx) => (
            <div key={idx} className="flex items-center text-sm">
              <span className="text-gray-500 mr-3">{idx}:</span>
              <span className="text-gray-900">{formatCellValue(item)}</span>
            </div>
          ))}
        </div>

        {!showFullData && arr.length > 20 && (
          <div className="text-center text-sm text-gray-500">
            Showing first 20 of {arr.length} items
          </div>
        )}
      </div>
    );
  };

  const renderObject = (obj) => {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="space-y-2">
          {Object.entries(obj).map(([key, value]) => (
            <div key={key} className="flex items-start">
              <span className="text-sm font-medium text-gray-600 mr-3">{key}:</span>
              <span className="text-sm text-gray-900">{formatCellValue(value)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const formatCellValue = (value) => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">null</span>;
    }
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    if (typeof value === 'boolean') {
      return value.toString();
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return value.toString();
  };

  return (
    <div className="space-y-3">
      {renderResult()}
      
      {executionTime !== null && executionTime !== undefined && (
        <div className="flex items-center justify-end text-xs text-gray-500">
          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Executed in {executionTime}ms
        </div>
      )}
    </div>
  );
};

export default ResultVisualization;
