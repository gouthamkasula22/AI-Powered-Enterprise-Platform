import React, { useState, useEffect } from 'react';
import { debounce } from 'lodash';
import PasswordRequirements from './PasswordRequirements';
import PasswordStrengthMeter from './PasswordStrengthMeter';

const RegistrationForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [validation, setValidation] = useState({
    email: { isValid: true, message: '' },
    password: { isValid: true, message: '', requirements: [] },
    confirmPassword: { isValid: true, message: '' },
    form: { isValid: true, message: '' }
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [strengthLevel, setStrengthLevel] = useState('Weak');

  // Debounced validation for email to avoid too many requests
  const validateEmail = debounce(async (email) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/validate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const result = await response.json();
      
      setValidation(prev => ({
        ...prev,
        email: {
          isValid: result.is_available,
          message: result.is_available ? '' : 'Email is already in use'
        }
      }));
    } catch (error) {
      console.error('Email validation error:', error);
    }
  }, 500);
  
  // Validate password strength and requirements
  const validatePassword = async (password) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/validate-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, email: formData.email })
      });
      
      const result = await response.json();
      
      setPasswordStrength(result.score || 0);
      
      // Set strength level based on score
      if (result.score >= 80) setStrengthLevel('Very Strong');
      else if (result.score >= 60) setStrengthLevel('Strong');
      else if (result.score >= 40) setStrengthLevel('Good');
      else if (result.score >= 20) setStrengthLevel('Fair');
      else setStrengthLevel('Weak');
      
      // Convert requirements object to array if needed
      const requirementsArray = result.requirements 
        ? Object.entries(result.requirements).map(([name, is_met]) => ({
            name,
            is_met,
            description: name
              .replace(/([A-Z])/g, ' $1')
              .replace(/^./, str => str.toUpperCase())
          }))
        : [];
      
      setValidation(prev => ({
        ...prev,
        password: {
          isValid: result.is_valid,
          message: result.is_valid ? '' : 'Password does not meet requirements',
          requirements: requirementsArray
        }
      }));
    } catch (error) {
      console.error('Password validation error:', error);
    }
  };
  
  // Validate confirm password
  const validateConfirmPassword = () => {
    const isValid = formData.password === formData.confirmPassword;
    
    setValidation(prev => ({
      ...prev,
      confirmPassword: {
        isValid,
        message: isValid ? '' : 'Passwords do not match'
      }
    }));
  };
  
  // Validate form on data changes
  useEffect(() => {
    if (formData.email) {
      validateEmail(formData.email);
    }
  }, [formData.email]);
  
  useEffect(() => {
    if (formData.password) {
      validatePassword(formData.password);
    }
  }, [formData.password]);
  
  useEffect(() => {
    if (formData.confirmPassword) {
      validateConfirmPassword();
    }
  }, [formData.confirmPassword, formData.password]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Final validation
    const isEmailValid = validation.email.isValid && formData.email.trim() !== '';
    const isPasswordValid = validation.password.isValid && formData.password.trim() !== '';
    const isConfirmPasswordValid = validation.confirmPassword.isValid && formData.confirmPassword.trim() !== '';
    
    const isFormValid = isEmailValid && isPasswordValid && isConfirmPasswordValid;
    
    setValidation(prev => ({
      ...prev,
      form: {
        isValid: isFormValid,
        message: isFormValid ? '' : 'Please fix the errors before submitting'
      }
    }));
    
    if (!isFormValid) return;
    
    setIsSubmitting(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        onSuccess && onSuccess(result);
      } else {
        const error = await response.json();
        setValidation(prev => ({
          ...prev,
          form: {
            isValid: false,
            message: error.detail?.message || 'Registration failed. Please try again.'
          }
        }));
      }
    } catch (error) {
      console.error('Registration error:', error);
      setValidation(prev => ({
        ...prev,
        form: {
          isValid: false,
          message: 'An error occurred. Please try again later.'
        }
      }));
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <div className="mt-1">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={handleChange}
            className={`appearance-none block w-full px-3 py-2 border ${
              validation.email.isValid ? 'border-gray-300' : 'border-red-500'
            } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
          />
        </div>
        {!validation.email.isValid && (
          <p className="mt-2 text-sm text-red-600">
            {validation.email.message}
          </p>
        )}
      </div>
      
      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <div className="mt-1">
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={formData.password}
            onChange={handleChange}
            className={`appearance-none block w-full px-3 py-2 border ${
              validation.password.isValid ? 'border-gray-300' : 'border-red-500'
            } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
          />
        </div>
        
        {/* Password Strength Meter */}
        {formData.password && (
          <div className="mt-2">
            <PasswordStrengthMeter 
              strengthScore={passwordStrength} 
              strengthLevel={strengthLevel}
              isVisible={!!formData.password} 
            />
          </div>
        )}
        
        {/* Password Requirements */}
        {formData.password && (
          <div className="mt-2">
            <PasswordRequirements 
              requirements={validation.password.requirements} 
              isVisible={!!formData.password} 
            />
          </div>
        )}
        
        {!validation.password.isValid && (
          <p className="mt-2 text-sm text-red-600">
            {validation.password.message}
          </p>
        )}
      </div>
      
      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
          Confirm Password
        </label>
        <div className="mt-1">
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            value={formData.confirmPassword}
            onChange={handleChange}
            className={`appearance-none block w-full px-3 py-2 border ${
              validation.confirmPassword.isValid ? 'border-gray-300' : 'border-red-500'
            } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
          />
        </div>
        {!validation.confirmPassword.isValid && (
          <p className="mt-2 text-sm text-red-600">
            {validation.confirmPassword.message}
          </p>
        )}
      </div>
      
      {/* Form Error */}
      {!validation.form.isValid && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {validation.form.message}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? 'Registering...' : 'Register'}
        </button>
      </div>
    </form>
  );
};

export default RegistrationForm;