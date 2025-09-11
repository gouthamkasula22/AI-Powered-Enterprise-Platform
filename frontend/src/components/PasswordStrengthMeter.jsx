import React from 'react';

const PasswordStrengthMeter = ({ strengthScore = 0, strengthLevel = 'Weak', isVisible = true }) => {
  if (!isVisible) return null;

  const getStrengthColor = (level) => {
    switch (level) {
      case 'Very Strong': return 'bg-green-600';
      case 'Strong': return 'bg-green-500';
      case 'Good': return 'bg-yellow-500';
      case 'Fair': return 'bg-orange-500';
      case 'Weak': return 'bg-red-500';
      default: return 'bg-gray-300';
    }
  };

  const getTextColor = (level) => {
    switch (level) {
      case 'Very Strong': return 'text-green-700';
      case 'Strong': return 'text-green-600';
      case 'Good': return 'text-yellow-600';
      case 'Fair': return 'text-orange-600';
      case 'Weak': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="mt-2">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-gray-600">Password Strength</span>
        <span className={`text-xs font-medium ${getTextColor(strengthLevel)}`}>
          {strengthLevel} ({strengthScore}/100)
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${getStrengthColor(strengthLevel)}`}
          style={{ width: `${strengthScore}%` }}
        />
      </div>
    </div>
  );
};

export default PasswordStrengthMeter;
