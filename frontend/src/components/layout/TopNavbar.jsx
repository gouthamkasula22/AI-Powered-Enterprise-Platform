import { useAuth } from '../../contexts/AuthContext';
import { Fragment } from 'react';

// Need to install @headlessui/react for Menu component
// For now, let's create a simpler version without it
const TopNavbar = ({ onMenuClick, onContextPanelClick }) => {
  const { user, logout } = useAuth();
  
  return (
    <header className="bg-white border-b border-gray-200 flex items-center h-16 px-4">
      <button 
        onClick={onMenuClick}
        className="mr-4 text-gray-500 hover:text-gray-700 focus:outline-none"
        aria-label="Toggle sidebar"
      >
        <span className="material-icons-outlined">menu</span>
      </button>
      
      <div className="flex-1">
        {/* Breadcrumbs or page title could go here */}
      </div>
      
      <div className="flex items-center space-x-4">
        <button 
          onClick={onContextPanelClick}
          className="text-gray-500 hover:text-gray-700 focus:outline-none"
          aria-label="Toggle context panel"
        >
          <span className="material-icons-outlined">help_outline</span>
        </button>
        
        <div className="relative">
          <button 
            className="flex items-center text-sm focus:outline-none"
            aria-label="User menu"
            onClick={() => {
              // Simple dropdown toggle - will be replaced with headlessui/react Menu
              const dropdown = document.getElementById('user-dropdown');
              if (dropdown) {
                dropdown.classList.toggle('hidden');
              }
            }}
          >
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              {user?.first_name?.[0] || user?.email?.[0] || 'U'}
            </div>
          </button>
          
          <div 
            id="user-dropdown"
            className="hidden absolute right-0 w-48 mt-2 origin-top-right bg-white divide-y divide-gray-100 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
          >
            <div className="px-1 py-1">
              <a
                href="/profile"
                className="group flex items-center w-full px-3 py-2 text-sm hover:bg-gray-100"
              >
                Profile
              </a>
              <button
                onClick={logout}
                className="group flex items-center w-full px-3 py-2 text-sm text-red-600 hover:bg-gray-100"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopNavbar;