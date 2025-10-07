/**
 * Sheet Selector Component
 * 
 * Displays tabs for switching between Excel sheets.
 */

import React from 'react';

const SheetSelector = ({ sheets, selectedSheet, onSheetChange }) => {
  if (!sheets || sheets.length === 0) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Sheets</h3>
      
      <div className="flex flex-wrap gap-2">
        {sheets.map((sheet) => (
          <button
            key={sheet.id}
            onClick={() => onSheetChange(sheet)}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${
                selectedSheet?.id === sheet.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            <div className="flex items-center space-x-2">
              <span>{sheet.sheet_name}</span>
              <span className="text-xs opacity-75">
                ({sheet.row_count} × {sheet.column_count})
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Sheet Statistics */}
      {selectedSheet && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Rows:</span>
              <span className="ml-2 font-medium text-gray-900">
                {selectedSheet.row_count.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Columns:</span>
              <span className="ml-2 font-medium text-gray-900">
                {selectedSheet.column_count}
              </span>
            </div>
            {selectedSheet.has_missing_values && (
              <div>
                <span className="text-gray-600">Missing:</span>
                <span className="ml-2 font-medium text-yellow-600">
                  {selectedSheet.missing_percentage}%
                </span>
              </div>
            )}
            {selectedSheet.duplicate_rows > 0 && (
              <div>
                <span className="text-gray-600">Duplicates:</span>
                <span className="ml-2 font-medium text-orange-600">
                  {selectedSheet.duplicate_rows}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SheetSelector;
