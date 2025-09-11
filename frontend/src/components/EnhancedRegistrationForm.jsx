import React, { useState, useEffect } from 'react';
import PasswordRequirements from './PasswordRequirements';
import PasswordStrengthMeter from './PasswordStrengthMeter';

const EnhancedRegistrationForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [validation, setValidation] = useState({
    email: { isValid: null, message: '', suggestion: '' },
    password: { 
      isValid: null, 
      strengthScore: 0, 
      strengthLevel: 'Weak',
      requirements: [],
      suggestions: [],
      estimatedCrackTime: ''
    }
  });
  
  const [showRequirements, setShowRequirements] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');

  // Debounced validation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.email) {
        validateEmail(formData.email);
      }
      if (formData.password) {
        validatePassword(formData.password, formData.email);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [formData.email, formData.password]);

  const validateEmail = async (email) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/validate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const result = await response.json();
      
      setValidation(prev => ({
        ...prev,
        email: {
          isValid: result.is_valid,
          message: result.reason || (result.is_valid ? 'Valid email' : 'Invalid email'),
          suggestion: result.suggestion || ''
        }
      }));
    } catch (error) {
      console.error('Email validation error:', error);
    }
  };

  const validatePassword = async (password, email = '') => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/validate-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, email })
      });
      
      const result = await response.json();
      
      setValidation(prev => ({
        ...prev,
        password: {
          isValid: result.is_valid,
          strengthScore: result.strength_score,
          strengthLevel: result.strength_level,
          requirements: result.requirements,
          suggestions: result.suggestions,
          estimatedCrackTime: result.estimated_crack_time
        }
      }));
    } catch (error) {
      console.error('Password validation error:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (name === 'password') {
      setShowRequirements(value.length > 0);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      setSubmitMessage('Passwords do not match');
      return;
    }
    
    if (!validation.email.isValid || !validation.password.isValid) {
      setSubmitMessage('Please fix validation errors before submitting');
      return;
    }
    
    setIsSubmitting(true);
    setSubmitMessage('');
    
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSubmitMessage('Registration successful! Welcome!');
        // Redirect or handle success
      } else {
        const error = await response.json();
        setSubmitMessage(error.error?.message || 'Registration failed');
      }
    } catch (error) {
      setSubmitMessage('Network error. Please try again.');
      console.error('Registration error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getInputClassName = (field) => {
    const baseClass = "mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm";
    
    if (validation[field]?.isValid === null) {
      return `${baseClass} border-gray-300`;
    }
    
    return validation[field]?.isValid 
      ? `${baseClass} border-green-500 focus:border-green-500 focus:ring-green-500`
      : `${baseClass} border-red-500 focus:border-red-500 focus:ring-red-500`;
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center text-gray-900 mb-6">Create Account</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className={getInputClassName('email')}
            placeholder="Enter your email"
            required
          />
          {validation.email.isValid === false && (
            <div className="mt-1">
              <p className="text-xs text-red-600">{validation.email.message}</p>
              {validation.email.suggestion && (
                <p className="text-xs text-blue-600">
                  Did you mean: {validation.email.suggestion}?
                </p>
              )}
            </div>
          )}
          {validation.email.isValid === true && (
            <p className="mt-1 text-xs text-green-600">Valid email address</p>
          )}
        </div>

        {/* Password Field */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className={getInputClassName('password')}
            placeholder="Create a strong password"
            required
          />
          
          {/* Password Strength Meter */}
          <PasswordStrengthMeter 
            strengthScore={validation.password.strengthScore}
            strengthLevel={validation.password.strengthLevel}
            isVisible={formData.password.length > 0}
          />
          
          {/* Password Requirements */}
          <PasswordRequirements 
            requirements={validation.password.requirements}
            isVisible={showRequirements}
          />
          
          {/* Password Suggestions */}
          {validation.password.suggestions.length > 0 && (
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-xs font-medium text-blue-800 mb-1">Suggestions:</p>
              <ul className="text-xs text-blue-700 space-y-1">
                {validation.password.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-blue-500 mr-1">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Crack Time Estimate */}
          {validation.password.estimatedCrackTime && formData.password.length > 0 && (
            <p className="mt-1 text-xs text-gray-600">
              Estimated crack time: <span className="font-medium">{validation.password.estimatedCrackTime}</span>
            </p>
          )}
        </div>

        {/* Confirm Password Field */}
        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
            Confirm Password
          </label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Confirm your password"
            required
          />
          {formData.confirmPassword && formData.password !== formData.confirmPassword && (
            <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || !validation.email.isValid || !validation.password.isValid}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            isSubmitting || !validation.email.isValid || !validation.password.isValid
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
          }`}
        >
          {isSubmitting ? 'Creating Account...' : 'Create Account'}
        </button>

        {/* Submit Message */}
        {submitMessage && (
          <div className={`mt-2 p-2 rounded-md ${
            submitMessage.includes('successful') 
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            <p className="text-sm">{submitMessage}</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default EnhancedRegistrationForm;
