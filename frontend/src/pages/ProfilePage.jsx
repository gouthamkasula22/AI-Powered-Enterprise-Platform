import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const ProfilePage = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: user?.bio || '',
    profileImage: user?.profileImage || ''
  });
  const [isEditing, setIsEditing] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would update the user profile via API
    console.log('Profile update:', formData);
    
    // Mock successful update
    setTimeout(() => {
      setIsEditing(false);
      alert('Profile updated successfully');
    }, 800);
  };
  
  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-gray-700 to-gray-600 p-6">
            <div className="flex items-center">
              <div className="w-20 h-20 rounded-full bg-gray-500 flex items-center justify-center text-3xl font-semibold mr-4">
                {user?.name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <div>
                <h1 className="text-2xl font-bold">{user?.name || 'User'}</h1>
                <p className="text-gray-300">{user?.email || 'user@example.com'}</p>
                <div className="mt-2">
                  <span className="bg-green-800/40 text-green-400 px-2 py-0.5 text-xs rounded-full">
                    Active Account
                  </span>
                </div>
              </div>
              {!isEditing && (
                <button 
                  onClick={() => setIsEditing(true)}
                  className="ml-auto bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded-md transition-colors"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>
          
          <div className="p-6">
            {!isEditing ? (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-2">Profile Information</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-400">Name</p>
                        <p>{user?.name || 'Not set'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-400">Email</p>
                        <p>{user?.email || 'Not set'}</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Biography</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p>{user?.bio || 'No biography provided.'}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Account Information</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-400">Account created</p>
                        <p>September 15, 2025</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-400">Account type</p>
                        <p>Standard User</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-400">Last login</p>
                        <p>Today, 10:30 AM</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-2">Edit Profile Information</h3>
                  <div className="bg-gray-700 rounded-lg p-4 space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Name</label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Email</label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                        disabled
                      />
                      <p className="text-xs text-gray-400 mt-1">Email cannot be changed directly. Contact support for email changes.</p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Edit Biography</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <textarea
                      name="bio"
                      value={formData.bio}
                      onChange={handleChange}
                      rows="4"
                      className="w-full bg-gray-600 border border-gray-500 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      placeholder="Tell us about yourself..."
                    ></textarea>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-orange-500 hover:bg-orange-600 px-4 py-2 rounded-md transition-colors"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;