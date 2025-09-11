import React from 'react';

const PasswordRequirements = ({ requirements = [], isVisible = true }) => {
  if (!isVisible || !requirements.length) return null;

  return (
    <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
      <h4 className="text-sm font-medium text-gray-700 mb-2">Password Requirements:</h4>
      <ul className="space-y-1">
        {requirements.map((req) => (
          <li key={req.name} className="flex items-center text-xs">
            <span 
              className={`inline-block w-3 h-3 rounded-full mr-2 flex-shrink-0 ${
                req.is_met 
                  ? 'bg-green-500' 
                  : 'bg-gray-300'
              }`}
            />
            <span className={req.is_met ? 'text-green-700' : 'text-gray-600'}>
              {req.description}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PasswordRequirements;
