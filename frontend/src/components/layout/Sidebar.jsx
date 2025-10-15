import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { NavLink } from 'react-router-dom';
import { RoleGuard } from '../ProtectedRoute';

const Sidebar = ({ isOpen }) => {
  const { user } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  
  return (
    <aside className={`
      ${isOpen ? 'w-64' : 'w-16'} 
      transition-width duration-300 ease-in-out
      ${isDarkMode ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'}
      border-r h-full flex flex-col
    `}>
      <div className={`p-4 ${isDarkMode ? 'border-gray-700' : 'border-gray-100'} border-b`}>
        <img 
          src="/logo.svg" 
          alt="Logo" 
          className={`mx-auto h-8 ${!isOpen && 'w-8'}`}
        />
      </div>
      
      <nav className="flex-1 pt-4">
        <ul className="space-y-1">
          <li>
            <NavLink 
              to="/chat/new" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive 
                  ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                  : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                }
                rounded-none border-l-4
                ${isActive 
                  ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                  : 'border-transparent'
                }
              `}
              end
            >
              <span className="material-icons-outlined text-xl mr-3">chat</span>
              {isOpen && <span>Chat Assistant</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/excel" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive 
                  ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                  : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                }
                rounded-none border-l-4
                ${isActive 
                  ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                  : 'border-transparent'
                }
              `}
            >
              <span className="material-icons-outlined text-xl mr-3">table_chart</span>
              {isOpen && <span>Excel Q&A</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/images/generate" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive 
                  ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                  : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                }
                rounded-none border-l-4
                ${isActive 
                  ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                  : 'border-transparent'
                }
              `}
            >
              <span className="material-icons-outlined text-xl mr-3">image</span>
              {isOpen && <span>Generate Images</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/images/gallery" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive 
                  ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                  : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                }
                rounded-none border-l-4
                ${isActive 
                  ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                  : 'border-transparent'
                }
              `}
            >
              <span className="material-icons-outlined text-xl mr-3">photo_library</span>
              {isOpen && <span>Gallery</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/profile" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive 
                  ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                  : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                }
                rounded-none border-l-4
                ${isActive 
                  ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                  : 'border-transparent'
                }
              `}
            >
              <span className="material-icons-outlined text-xl mr-3">person</span>
              {isOpen && <span>Profile</span>}
            </NavLink>
          </li>
          
          <RoleGuard roles={['admin', 'super_admin']}>
            <li>
              <NavLink 
                to="/admin" 
                className={({ isActive }) => `
                  flex items-center px-4 py-3 text-sm
                  ${isActive 
                    ? isDarkMode ? 'bg-gray-800 text-orange-500' : 'bg-gray-50 text-blue-600'
                    : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                  }
                  rounded-none border-l-4
                  ${isActive 
                    ? isDarkMode ? 'border-orange-500' : 'border-blue-500'
                    : 'border-transparent'
                  }
                `}
              >
                <span className="material-icons-outlined text-xl mr-3">admin_panel_settings</span>
                {isOpen && <span>Admin</span>}
              </NavLink>
            </li>
          </RoleGuard>
        </ul>
      </nav>
      
      <div className={`p-4 space-y-3 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'} border-t`}>
        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className={`
            w-full flex items-center justify-center px-3 py-2 rounded-lg text-sm transition-colors
            ${isDarkMode 
              ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
          title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          <span className="material-icons-outlined text-lg">
            {isDarkMode ? 'light_mode' : 'dark_mode'}
          </span>
          {isOpen && (
            <span className="ml-2">
              {isDarkMode ? 'Light Mode' : 'Dark Mode'}
            </span>
          )}
        </button>

        {/* User Profile */}
        <div className="flex items-center">
          <div className={`w-8 h-8 rounded-full ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'} flex items-center justify-center font-medium`}>
            {user?.first_name?.[0] || user?.email?.[0] || 'U'}
          </div>
          {isOpen && (
            <div className="ml-3 truncate">
              <div className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                {user?.full_name || user?.email}
              </div>
              <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {user?.role}
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;