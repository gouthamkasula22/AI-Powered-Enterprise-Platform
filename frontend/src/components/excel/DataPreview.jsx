/**
 * Data Preview Component
 * 
 * Displays a preview of Excel sheet data in a table.
 */

import React from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

const DataPreview = ({ data, selectedSheet }) => {
  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-8 text-center">
        <p className="text-gray-500">No data to preview</p>
      </div>
    );
  }

  // Create column definitions
  const columnDefs = data.column_names.map((colName) => ({
    field: colName,
    headerName: colName,
    sortable: true,
    filter: true,
    resizable: true,
    minWidth: 120,
    cellStyle: (params) => {
      // Highlight null values
      if (params.value === null || params.value === undefined || params.value === '') {
        return { backgroundColor: '#FEF3C7', color: '#92400E' };
      }
      return null;
    },
    valueFormatter: (params) => {
      if (params.value === null || params.value === undefined) {
        return '(null)';
      }
      if (params.value === '') {
        return '(empty)';
      }
      return params.value;
    },
  }));

  const defaultColDef = {
    flex: 1,
    minWidth: 100,
    sortable: true,
    filter: true,
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Data Preview
          </h3>
          <span className="text-sm text-gray-500">
            Showing {data.preview_size} of {data.rows.toLocaleString()} rows
          </span>
        </div>
      </div>

      <div className="ag-theme-alpine" style={{ height: 600, width: '100%' }}>
        <AgGridReact
          rowData={data.data}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          animateRows={true}
          pagination={true}
          paginationPageSize={20}
          domLayout="normal"
        />
      </div>

      {/* Column Information */}
      {selectedSheet?.statistics && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <details className="text-sm">
            <summary className="font-medium text-gray-700 cursor-pointer hover:text-gray-900">
              Column Statistics
            </summary>
            <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
              {Object.entries(selectedSheet.statistics.columns || {}).slice(0, 10).map(([col, stats]) => (
                <div key={col} className="flex items-start space-x-3 text-xs">
                  <span className="font-medium text-gray-700 min-w-[120px]">{col}:</span>
                  <div className="flex-1 text-gray-600">
                    {stats.data_type === 'numeric' && (
                      <span>
                        Min: {stats.min?.toFixed(2)}, Max: {stats.max?.toFixed(2)}, 
                        Mean: {stats.mean?.toFixed(2)}
                      </span>
                    )}
                    {stats.data_type === 'text' && (
                      <span>
                        {stats.unique_count} unique values, 
                        Avg length: {stats.avg_length}
                      </span>
                    )}
                    {stats.data_type === 'boolean' && (
                      <span>
                        True: {stats.true_count}, False: {stats.false_count}
                      </span>
                    )}
                    {stats.null_count > 0 && (
                      <span className="text-yellow-600 ml-2">
                        ({stats.null_count} nulls)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default DataPreview;
