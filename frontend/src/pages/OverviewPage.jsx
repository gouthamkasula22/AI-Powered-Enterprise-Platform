import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

const OverviewPage = () => {
  const { user } = useAuth();
  
  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-semibold mb-6">Overview</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link 
              to="/profile" 
              className="bg-gray-700 hover:bg-gray-600 transition-colors p-6 rounded-lg flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-full bg-gray-600 mb-4 flex items-center justify-center text-2xl">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-xl font-medium mb-2">Profile</h2>
              <p className="text-gray-300 text-sm text-center">
                View and update your personal information
              </p>
            </Link>
            
            <Link 
              to="/chat/new" 
              className="bg-gray-700 hover:bg-gray-600 transition-colors p-6 rounded-lg flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-full bg-purple-900/30 mb-4 flex items-center justify-center text-2xl">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h2 className="text-xl font-medium mb-2">Chat Assistant</h2>
              <p className="text-gray-300 text-sm text-center">
                Get help with authentication and security
              </p>
            </Link>
            
            <Link 
              to="/security" 
              className="bg-gray-700 hover:bg-gray-600 transition-colors p-6 rounded-lg flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-full bg-gray-600 mb-4 flex items-center justify-center text-2xl">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h2 className="text-xl font-medium mb-2">Security</h2>
              <p className="text-gray-300 text-sm text-center">
                Manage your security settings
              </p>
            </Link>
          </div>
          
          <div className="mt-10">
            <h2 className="text-2xl font-semibold mb-4">Account Summary</h2>
            <div className="bg-gray-700 rounded-lg p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium mb-2">Profile Status</h3>
                  <ul className="space-y-2">
                    <li className="flex items-center">
                      <div className="w-4 h-4 rounded-full bg-green-500 mr-2"></div>
                      <span>Account Active</span>
                    </li>
                    <li className="flex items-center">
                      <div className="w-4 h-4 rounded-full bg-yellow-500 mr-2"></div>
                      <span>Email Verification: {user?.emailVerified ? 'Verified' : 'Pending'}</span>
                    </li>
                    <li className="flex items-center">
                      <div className="w-4 h-4 rounded-full bg-red-500 mr-2"></div>
                      <span>Two-Factor Authentication: Not Enabled</span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Recent Activity</h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center justify-between">
                      <span>Last Login</span>
                      <span className="text-gray-300">Today, 10:30 AM</span>
                    </li>
                    <li className="flex items-center justify-between">
                      <span>Password Changed</span>
                      <span className="text-gray-300">30 days ago</span>
                    </li>
                    <li className="flex items-center justify-between">
                      <span>Profile Updated</span>
                      <span className="text-gray-300">45 days ago</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewPage;