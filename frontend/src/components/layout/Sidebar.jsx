import { useAuth } from '../../contexts/AuthContext';
import { NavLink } from 'react-router-dom';
import { RoleGuard } from '../ProtectedRoute';

const Sidebar = ({ isOpen }) => {
  const { user } = useAuth();
  
  return (
    <aside className={`
      ${isOpen ? 'w-64' : 'w-16'} 
      transition-width duration-300 ease-in-out
      bg-white border-r border-gray-200 h-full flex flex-col
    `}>
      <div className="p-4 border-b border-gray-100">
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
              to="/dashboard" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive ? 'bg-gray-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
                rounded-none border-l-4
                ${isActive ? 'border-blue-500' : 'border-transparent'}
              `}
              end
            >
              <span className="material-icons-outlined text-xl mr-3">dashboard</span>
              {isOpen && <span>Dashboard</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/chat/new" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive ? 'bg-gray-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
                rounded-none border-l-4
                ${isActive ? 'border-blue-500' : 'border-transparent'}
              `}
              end
            >
              <span className="material-icons-outlined text-xl mr-3">chat</span>
              {isOpen && <span>Chat Assistant</span>}
            </NavLink>
          </li>
          
          <li>
            <NavLink 
              to="/profile" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive ? 'bg-gray-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
                rounded-none border-l-4
                ${isActive ? 'border-blue-500' : 'border-transparent'}
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
                  ${isActive ? 'bg-gray-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
                  rounded-none border-l-4
                  ${isActive ? 'border-blue-500' : 'border-transparent'}
                `}
              >
                <span className="material-icons-outlined text-xl mr-3">admin_panel_settings</span>
                {isOpen && <span>Admin</span>}
              </NavLink>
            </li>
          </RoleGuard>
        </ul>
      </nav>
      
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
            {user?.first_name?.[0] || user?.email?.[0] || 'U'}
          </div>
          {isOpen && (
            <div className="ml-3 truncate">
              <div className="text-sm font-medium">{user?.full_name || user?.email}</div>
              <div className="text-xs text-gray-500">{user?.role}</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;