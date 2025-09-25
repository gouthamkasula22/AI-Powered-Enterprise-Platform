import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const SecurityPage = () => {
  const { user } = useAuth();
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    // Here you would update the password via API
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('New passwords do not match');
      return;
    }
    
    console.log('Password update:', passwordData);
    
    // Mock successful update
    setTimeout(() => {
      alert('Password updated successfully');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    }, 800);
  };
  
  const handleToggle2FA = () => {
    if (twoFactorEnabled) {
      // Disable 2FA logic would go here
      setTwoFactorEnabled(false);
      setShowQRCode(false);
    } else {
      // Show QR code for setup
      setShowQRCode(true);
    }
  };
  
  const handleVerify2FA = (e) => {
    e.preventDefault();
    // Here you would verify the 2FA code via API
    console.log('2FA verification:', verificationCode);
    
    // Mock successful verification
    setTimeout(() => {
      setTwoFactorEnabled(true);
      setShowQRCode(false);
      setVerificationCode('');
      alert('Two-factor authentication enabled successfully');
    }, 800);
  };
  
  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-semibold mb-6">Security Settings</h1>
          
          <div className="space-y-10">
            {/* Password Change Section */}
            <div>
              <h2 className="text-xl font-medium mb-4">Password</h2>
              <div className="bg-gray-700 rounded-lg p-6">
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Current Password</label>
                    <input
                      type="password"
                      name="currentPassword"
                      value={passwordData.currentPassword}
                      onChange={handlePasswordChange}
                      className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">New Password</label>
                    <input
                      type="password"
                      name="newPassword"
                      value={passwordData.newPassword}
                      onChange={handlePasswordChange}
                      className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Confirm New Password</label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={passwordData.confirmPassword}
                      onChange={handlePasswordChange}
                      className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  
                  <div className="pt-2">
                    <button
                      type="submit"
                      className="bg-orange-500 hover:bg-orange-600 px-4 py-2 rounded-md transition-colors"
                    >
                      Update Password
                    </button>
                  </div>
                </form>
              </div>
            </div>
            
            {/* Two-Factor Authentication Section */}
            <div>
              <h2 className="text-xl font-medium mb-4">Two-Factor Authentication</h2>
              <div className="bg-gray-700 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">
                      {twoFactorEnabled ? 'Two-factor authentication is enabled' : 'Enable two-factor authentication'}
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">
                      Add an extra layer of security to your account by requiring a verification code in addition to your password.
                    </p>
                  </div>
                  <button
                    onClick={handleToggle2FA}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      twoFactorEnabled 
                        ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                        : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                    }`}
                  >
                    {twoFactorEnabled ? 'Disable' : 'Enable'}
                  </button>
                </div>
                
                {showQRCode && (
                  <div className="mt-6 border-t border-gray-600 pt-6">
                    <h3 className="font-medium mb-4">Set up two-factor authentication</h3>
                    <div className="flex flex-col md:flex-row gap-6">
                      <div>
                        <p className="text-sm text-gray-400 mb-2">1. Scan this QR code with your authenticator app</p>
                        <div className="bg-white p-4 w-48 h-48 flex items-center justify-center text-black">
                          QR Code Placeholder
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-400 mb-2">2. Enter the verification code from your app</p>
                        <form onSubmit={handleVerify2FA} className="space-y-4">
                          <input
                            type="text"
                            value={verificationCode}
                            onChange={(e) => setVerificationCode(e.target.value)}
                            placeholder="Enter 6-digit code"
                            className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                            required
                          />
                          <button
                            type="submit"
                            className="bg-orange-500 hover:bg-orange-600 px-4 py-2 rounded-md transition-colors"
                          >
                            Verify and Enable
                          </button>
                        </form>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Sessions Section */}
            <div>
              <h2 className="text-xl font-medium mb-4">Active Sessions</h2>
              <div className="bg-gray-700 rounded-lg p-6">
                <div className="space-y-4">
                  <div className="border-b border-gray-600 pb-4 flex items-center justify-between">
                    <div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        <h3 className="font-medium">Current Session</h3>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">Windows • Chrome • Sep 24, 2025 10:30 AM</p>
                    </div>
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">Current</span>
                  </div>
                  
                  <div className="border-b border-gray-600 pb-4 flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Session on iPhone</h3>
                      <p className="text-sm text-gray-400 mt-1">iOS • Safari • Sep 23, 2025 8:45 PM</p>
                    </div>
                    <button className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded hover:bg-red-500/30">
                      Log Out
                    </button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Session on MacBook</h3>
                      <p className="text-sm text-gray-400 mt-1">macOS • Firefox • Sep 22, 2025 3:20 PM</p>
                    </div>
                    <button className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded hover:bg-red-500/30">
                      Log Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityPage;