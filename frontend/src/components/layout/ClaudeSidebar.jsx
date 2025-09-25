import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import axios from 'axios';
// import { useMockAuth } from '../../contexts/MockAuthContext'; // For testing

const ClaudeSidebar = ({ isOpen }) => {
  const { user, logout, token } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  // Function to fetch chat history
  const fetchChatHistory = async () => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null); // Clear any previous errors
    try {
      const response = await axios.get('/api/conversations', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: 1,
          per_page: 10,
          sort: 'updated_at:desc'
        }
      });

      // Format data for our UI
      const conversations = response.data.conversations.map(conv => ({
        id: conv.id,
        title: conv.title || 'Untitled Conversation',
        date: formatDate(conv.updated_at || conv.created_at)
      }));
      
      setChatHistory(conversations);
    } catch (err) {
      console.error('Error fetching chat history:', err);
      
      // Show different error messages based on the error type
      if (err.response) {
        // Server responded with an error status
        if (err.response.status === 401 || err.response.status === 403) {
          // Auth issues
          setError('Please log in again to view your chat history');
        } else {
          setError(`Couldn't load chats (${err.response.status})`);
        }
      } else if (err.request) {
        // No response received
        setError('Network error: Could not reach server');
      } else {
        setError('Failed to load chat history');
      }
      
      // Fall back to mock data if API fails - only in development
      if (process.env.NODE_ENV === 'development') {
        const mockChatHistory = [
          { id: 1, title: "User authentication workflow", date: "Today" },
          { id: 2, title: "Database schema design", date: "Yesterday" },
          { id: 3, title: "API endpoints planning", date: "Sep 20" },
          { id: 4, title: "Frontend component architecture", date: "Sep 18" },
          { id: 5, title: "Security best practices", date: "Sep 15" }
        ];
        setChatHistory(mockChatHistory);
      } else {
        setChatHistory([]);
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  // Load chat history when component mounts or token changes
  useEffect(() => {
    fetchChatHistory();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps
  
  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };
  
  const sidebarClasses = isOpen 
    ? `fixed inset-y-0 left-0 w-64 ${isDarkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'} transform translate-x-0 transition-transform duration-300 ease-in-out z-30` 
    : `fixed inset-y-0 left-0 w-64 ${isDarkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'} transform -translate-x-full transition-transform duration-300 ease-in-out z-30`;
    
  return (
    <div className={sidebarClasses}>
      <div className="flex flex-col h-full">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-800 flex items-center">
          <span className="text-lg font-semibold">Chat Assistant</span>
        </div>
        
        {/* New Chat Button */}
        <div className="px-4 py-4">
          <Link
            to="/chat/new"
            className="flex items-center justify-center w-full px-4 py-2.5 text-center rounded-md bg-orange-500/10 text-orange-500 hover:bg-orange-500/20"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Chat
          </Link>
        </div>
        
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-4 py-2">
          <h3 className="px-2 text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            Chat History
          </h3>
          <div className="space-y-1">
            {isLoading ? (
              <div className="animate-pulse">
                <div className="h-10 bg-gray-800 rounded-md mb-2"></div>
                <div className="h-10 bg-gray-800 rounded-md mb-2"></div>
                <div className="h-10 bg-gray-800 rounded-md"></div>
              </div>
            ) : error ? (
              <div className="mt-2 px-3 py-4 text-center rounded-md bg-red-900/20 border border-red-900/30">
                <div className="text-red-400 text-sm mb-1">
                  <svg className="w-5 h-5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Error
                </div>
                <div className="text-gray-300 text-xs">{error}</div>
                <button 
                  onClick={() => fetchChatHistory()}
                  className="mt-2 text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded-md text-gray-300"
                >
                  Retry
                </button>
              </div>
            ) : (
              <>
                {chatHistory.map(chat => (
                  <Link
                    key={chat.id}
                    to={`/chat/${chat.id}`}
                    className="block px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-md cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate">{chat.title}</span>
                      <span className="text-xs text-gray-500">{chat.date}</span>
                    </div>
                  </Link>
                ))}
                {chatHistory.length === 0 && !isLoading && (
                  <div className="px-3 py-6 text-center text-sm text-gray-500">
                    No chat history yet
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        {/* Settings and Help Links */}
        <div className="mt-auto">
          <div className="px-4 py-2">
            <Link to="/user/help" className="flex items-center px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-md">
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Help & FAQ
            </Link>
          </div>
          
          <div className="px-4 py-2">
            <button 
              onClick={toggleTheme}
              className="flex items-center w-full px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-md"
            >
              {isDarkMode ? (
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
              {isDarkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </div>
        
        {/* User Profile Section */}
        <div className="border-t border-gray-800 p-4">
          <Link to="/user/profile" className="flex items-center w-full text-left hover:bg-gray-800 rounded-md p-2">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm mr-3">
              {user?.name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1">
              <p className="font-medium truncate">{user?.name || user?.email || 'User'}</p>
              <p className="text-xs text-gray-500">Account Settings</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ClaudeSidebar;