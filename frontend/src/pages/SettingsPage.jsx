import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const SettingsPage = () => {
  const { user } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    securityAlerts: true,
    productUpdates: false,
    marketingEmails: false
  });
  
  const [language, setLanguage] = useState('english');
  const [timezone, setTimezone] = useState('UTC');
  
  const handleNotificationChange = (e) => {
    const { name, checked } = e.target;
    setNotifications(prev => ({
      ...prev,
      [name]: checked
    }));
  };
  
  const handleSaveSettings = (e) => {
    e.preventDefault();
    // Here you would save the settings via API
    console.log('Settings update:', { notifications, language, timezone });
    
    // Mock successful update
    setTimeout(() => {
      alert('Settings updated successfully');
    }, 800);
  };
  
  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-semibold mb-6">Settings</h1>
          
          <form onSubmit={handleSaveSettings} className="space-y-10">
            {/* Appearance Settings */}
            <div>
              <h2 className="text-xl font-medium mb-4">Appearance</h2>
              <div className="bg-gray-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Theme</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Choose between light and dark mode
                    </p>
                  </div>
                  <div className="flex items-center">
                    <button
                      type="button"
                      onClick={toggleTheme}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        isDarkMode ? 'bg-orange-500' : 'bg-gray-400'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          isDarkMode ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    <span className="ml-2">{isDarkMode ? 'Dark' : 'Light'}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Notification Settings */}
            <div>
              <h2 className="text-xl font-medium mb-4">Notifications</h2>
              <div className="bg-gray-700 rounded-lg p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Email Notifications</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Receive notifications about your account via email
                    </p>
                  </div>
                  <div>
                    <input
                      type="checkbox"
                      id="emailNotifications"
                      name="emailNotifications"
                      checked={notifications.emailNotifications}
                      onChange={handleNotificationChange}
                      className="h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-500"
                    />
                  </div>
                </div>
                
                <div className="border-t border-gray-600 pt-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Security Alerts</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Get notified about important security events
                    </p>
                  </div>
                  <div>
                    <input
                      type="checkbox"
                      id="securityAlerts"
                      name="securityAlerts"
                      checked={notifications.securityAlerts}
                      onChange={handleNotificationChange}
                      className="h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-500"
                    />
                  </div>
                </div>
                
                <div className="border-t border-gray-600 pt-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Product Updates</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Stay informed about new features and improvements
                    </p>
                  </div>
                  <div>
                    <input
                      type="checkbox"
                      id="productUpdates"
                      name="productUpdates"
                      checked={notifications.productUpdates}
                      onChange={handleNotificationChange}
                      className="h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-500"
                    />
                  </div>
                </div>
                
                <div className="border-t border-gray-600 pt-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Marketing Emails</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      Receive promotional content and offers
                    </p>
                  </div>
                  <div>
                    <input
                      type="checkbox"
                      id="marketingEmails"
                      name="marketingEmails"
                      checked={notifications.marketingEmails}
                      onChange={handleNotificationChange}
                      className="h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-500"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Preferences */}
            <div>
              <h2 className="text-xl font-medium mb-4">Preferences</h2>
              <div className="bg-gray-700 rounded-lg p-6 space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="english">English</option>
                    <option value="spanish">Spanish</option>
                    <option value="french">French</option>
                    <option value="german">German</option>
                    <option value="japanese">Japanese</option>
                  </select>
                </div>
                
                <div className="border-t border-gray-600 pt-4">
                  <label className="block text-sm text-gray-400 mb-1">Timezone</label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="UTC">UTC (Coordinated Universal Time)</option>
                    <option value="EST">EST (Eastern Standard Time)</option>
                    <option value="CST">CST (Central Standard Time)</option>
                    <option value="MST">MST (Mountain Standard Time)</option>
                    <option value="PST">PST (Pacific Standard Time)</option>
                  </select>
                </div>
              </div>
            </div>
            
            {/* Data & Privacy */}
            <div>
              <h2 className="text-xl font-medium mb-4">Data & Privacy</h2>
              <div className="bg-gray-700 rounded-lg p-6 space-y-4">
                <div>
                  <h3 className="font-medium">Export Account Data</h3>
                  <p className="text-sm text-gray-400 mt-1">
                    Download a copy of your data including profile information and activity history
                  </p>
                  <button
                    type="button"
                    className="mt-2 bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded-md transition-colors text-sm"
                  >
                    Request Data Export
                  </button>
                </div>
                
                <div className="border-t border-gray-600 pt-4">
                  <h3 className="font-medium text-red-400">Delete Account</h3>
                  <p className="text-sm text-gray-400 mt-1">
                    Permanently delete your account and all associated data
                  </p>
                  <button
                    type="button"
                    className="mt-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 px-4 py-2 rounded-md transition-colors text-sm"
                  >
                    Delete My Account
                  </button>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end">
              <button
                type="submit"
                className="bg-orange-500 hover:bg-orange-600 px-6 py-2 rounded-md transition-colors"
              >
                Save Settings
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;