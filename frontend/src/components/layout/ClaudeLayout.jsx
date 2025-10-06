import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ClaudeSidebar from './ClaudeSidebar';
import ImageGallery from '../image/ImageGallery';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const ClaudeLayout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const { isDarkMode } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const toggleUserMenu = () => setIsUserMenuOpen(!isUserMenuOpen);
  const toggleLibrary = () => setIsLibraryOpen(!isLibraryOpen);
  
  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };
  
  return (
    <div className={`flex h-screen ${isDarkMode ? 'bg-black text-gray-100' : 'bg-white text-gray-900'}`}>
      {/* Sidebar */}
      <ClaudeSidebar isOpen={isSidebarOpen} />
      
      {/* Main Content */}
      <div className={`flex-1 flex flex-col ${isSidebarOpen ? 'ml-64' : 'ml-0'}`} 
           style={{ transition: 'margin-left 0.3s ease-in-out' }}>
        {/* Top Bar */}
        <div className={`${isDarkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} p-2 flex items-center border-b`}>
          <button 
            onClick={toggleSidebar}
            className="p-2 rounded-md text-gray-400 hover:bg-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <div className="mx-auto flex items-center">
            <div className="w-5 h-5 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs mr-1.5">
              C
            </div>
            <span className="text-sm font-medium">Chat Assistant</span>
          </div>
          
          {/* Library Button */}
          <button 
            onClick={toggleLibrary}
            className="p-2 rounded-md text-gray-400 hover:bg-gray-800 mr-2"
            title="Library"
          >
            <span className="material-icons-outlined text-xl">photo_library</span>
          </button>
          
          {/* User Menu */}
          <div className="ml-auto relative">
            <button 
              onClick={toggleUserMenu}
              className="flex items-center p-2 rounded-md hover:bg-gray-800"
            >
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm">
                {user?.first_name?.charAt(0) || user?.display_name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}
              </div>
            </button>
            
            {/* User Dropdown Menu */}
            {isUserMenuOpen && (
              <div className={`absolute right-0 top-full mt-1 w-64 ${isDarkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} border rounded-md shadow-lg z-50`}>
                <div className={`p-4 border-b ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                  <p className="font-medium">
                    {user?.display_name || `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'User'}
                  </p>
                  <p className="text-sm text-gray-400">{user?.email || 'user@example.com'}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {user?.role?.toLowerCase() === 'admin' ? 'Administrator' : 'User'}
                  </p>
                </div>
                
                <div className="py-2">
                  <Link to="/user/overview" className="flex items-center px-4 py-2 text-sm hover:bg-gray-800">
                    <svg className="w-5 h-5 mr-3 text-gray-400" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" fill="currentColor"/>
                    </svg>
                    Overview
                  </Link>
                  
                  <Link to="/chat/new" className="flex items-center px-4 py-2 text-sm hover:bg-gray-800">
                    <svg className="w-5 h-5 mr-3 text-gray-400" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Chat Assistant
                  </Link>
                  
                  <Link to="/user/profile" className="flex items-center px-4 py-2 text-sm hover:bg-gray-800">
                    <svg className="w-5 h-5 mr-3 text-gray-400" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                    </svg>
                    Profile
                  </Link>
                  
                  <Link to="/user/security" className="flex items-center px-4 py-2 text-sm hover:bg-gray-800">
                    <svg className="w-5 h-5 mr-3 text-gray-400" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" fill="currentColor"/>
                    </svg>
                    Security
                  </Link>
                  
                  <Link to="/user/settings" className="flex items-center px-4 py-2 text-sm hover:bg-gray-800">
                    <svg className="w-5 h-5 mr-3 text-gray-400" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor"/>
                    </svg>
                    Settings
                  </Link>
                  
                  <div className="border-t border-gray-800 my-1"></div>
                  
                  <button 
                    onClick={handleLogout}
                    className="flex w-full items-center px-4 py-2 text-sm text-red-500 hover:bg-gray-800"
                  >
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1">
          <div className={`h-full overflow-hidden ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
            {children}
          </div>
        </div>
      </div>
      
      {/* Library Side Panel */}
      {isLibraryOpen && (
        <>
          {/* Overlay */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={toggleLibrary}
          />
          
          {/* Side Panel */}
          <div className={`fixed right-0 top-0 h-full w-96 ${isDarkMode ? 'bg-gray-900' : 'bg-white'} shadow-2xl z-50 transform transition-transform duration-300 ease-in-out`}>
            <div className="flex flex-col h-full">
              {/* Panel Header */}
              <div className={`flex items-center justify-between p-4 border-b ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                <h2 className="text-lg font-semibold flex items-center">
                  <span className="material-icons-outlined text-xl mr-2">photo_library</span>
                  Library
                </h2>
                <button 
                  onClick={toggleLibrary}
                  className="p-1 rounded-md text-gray-400 hover:bg-gray-800"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Panel Content */}
              <div className="flex-1 overflow-y-auto p-4">
                <ImageGallery />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ClaudeLayout;