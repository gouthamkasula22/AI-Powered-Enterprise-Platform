# Claude-Style Dashboard Implementation Plan

## Overview

This document outlines the implementation plan for refactoring the user interface to create a professional Claude-style dashboard for the User Authentication Systems project. The design will follow Claude's aesthetic principles with a three-panel layout, minimal use of colors, and an emphasis on functionality and accessibility.

## Design Principles

1. **Minimalist Interface**: Clean design with adequate white space and minimal decorative elements
2. **Professional Typography**: Consistent font usage with clear hierarchy
3. **Three-Panel Layout**:
   - Left: Navigation sidebar
   - Center: Main content area
   - Right: Contextual information panel
4. **Muted Color Palette**: Primarily whites, grays, and subtle accent colors
5. **Responsive Design**: Adapts gracefully to different screen sizes
6. **Accessibility**: WCAG 2.1 AA compliance

## Implementation Roadmap

### Phase 1: Core Layout Components

#### 1. Dashboard Layout Structure

Create a responsive three-panel layout that forms the foundation of the Claude-style UI:

```jsx
// src/components/layout/DashboardLayout.jsx
import { useState } from 'react';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';
import ContextPanel from './ContextPanel';

const DashboardLayout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isContextPanelOpen, setIsContextPanelOpen] = useState(false);
  const [contextPanelContent, setContextPanelContent] = useState(null);
  
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const toggleContextPanel = () => setIsContextPanelOpen(!isContextPanelOpen);
  
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={isSidebarOpen} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopNavbar 
          onMenuClick={toggleSidebar} 
          onContextPanelClick={toggleContextPanel}
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-white">
          {children}
        </main>
      </div>
      <ContextPanel 
        isOpen={isContextPanelOpen}
        onClose={toggleContextPanel}
        content={contextPanelContent}
      />
    </div>
  );
};

export default DashboardLayout;
```

#### 2. Navigation Sidebar

Create a collapsible sidebar with navigation links styled in Claude's minimal aesthetic:

```jsx
// src/components/layout/Sidebar.jsx
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
              to="/chat" 
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm
                ${isActive ? 'bg-gray-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
                rounded-none border-l-4
                ${isActive ? 'border-blue-500' : 'border-transparent'}
              `}
            >
              <span className="material-icons-outlined text-xl mr-3">chat</span>
              {isOpen && <span>Chat</span>}
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
```

#### 3. Top Navigation Bar

Create a top navigation bar with user controls:

```jsx
// src/components/layout/TopNavbar.jsx
import { useAuth } from '../../contexts/AuthContext';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';

const TopNavbar = ({ onMenuClick, onContextPanelClick }) => {
  const { user, logout } = useAuth();
  
  return (
    <header className="bg-white border-b border-gray-200 flex items-center h-16 px-4">
      <button 
        onClick={onMenuClick}
        className="mr-4 text-gray-500 hover:text-gray-700 focus:outline-none"
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
        >
          <span className="material-icons-outlined">help_outline</span>
        </button>
        
        <Menu as="div" className="relative">
          <Menu.Button className="flex items-center text-sm focus:outline-none">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              {user?.first_name?.[0] || user?.email?.[0] || 'U'}
            </div>
          </Menu.Button>
          
          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <Menu.Items className="absolute right-0 w-48 mt-2 origin-top-right bg-white divide-y divide-gray-100 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <div className="px-1 py-1">
                <Menu.Item>
                  {({ active }) => (
                    <a
                      href="/profile"
                      className={`${
                        active ? 'bg-gray-100' : ''
                      } group flex items-center w-full px-3 py-2 text-sm`}
                    >
                      Profile
                    </a>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={logout}
                      className={`${
                        active ? 'bg-gray-100' : ''
                      } group flex items-center w-full px-3 py-2 text-sm text-red-600`}
                    >
                      Sign out
                    </button>
                  )}
                </Menu.Item>
              </div>
            </Menu.Items>
          </Transition>
        </Menu>
      </div>
    </header>
  );
};

export default TopNavbar;
```

#### 4. Context Panel

Create a contextual panel for showing help information, details, or related data:

```jsx
// src/components/layout/ContextPanel.jsx
const ContextPanel = ({ isOpen, onClose, content }) => {
  return (
    <div 
      className={`
        fixed inset-y-0 right-0 z-20 w-80 bg-white border-l border-gray-200
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        md:static md:translate-x-0 md:transition-none
        ${isOpen ? 'md:w-80' : 'md:w-0'}
      `}
    >
      <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
        <h3 className="text-lg font-medium text-gray-900">Details</h3>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 focus:outline-none"
        >
          <span className="material-icons-outlined">close</span>
        </button>
      </div>
      
      <div className="p-4 overflow-y-auto h-[calc(100%-4rem)]">
        {content || (
          <div className="text-center text-gray-500 mt-8">
            <p>Select an item to view details</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContextPanel;
```

### Phase 2: Chat Interface Components

#### 1. Chat Container

Main container for the chat interface:

```jsx
// src/components/chat/ChatContainer.jsx
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';
import ChatService from '../../services/ChatService';

const ChatContainer = () => {
  const { threadId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Fetch threads when component mounts
  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const response = await ChatService.getThreads();
        setThreads(response);
        
        // If no threadId in URL but we have threads, navigate to the most recent thread
        if (!threadId && response.length > 0) {
          navigate(`/chat/${response[0].id}`);
        }
      } catch (err) {
        setError('Failed to load conversations');
        console.error(err);
      }
    };
    
    fetchThreads();
  }, [navigate, threadId]);
  
  // Fetch messages when threadId changes
  useEffect(() => {
    if (!threadId) return;
    
    const fetchMessages = async () => {
      setIsLoading(true);
      try {
        const thread = await ChatService.getThread(threadId);
        setCurrentThread(thread);
        setMessages(thread.messages || []);
      } catch (err) {
        setError('Failed to load conversation');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchMessages();
  }, [threadId]);
  
  const handleSendMessage = async (content) => {
    // If no current thread, create one
    if (!currentThread) {
      try {
        const newThread = await ChatService.createThread({ 
          title: 'New Conversation',
          metadata: {}
        });
        setCurrentThread(newThread);
        navigate(`/chat/${newThread.id}`);
      } catch (err) {
        setError('Failed to create conversation');
        console.error(err);
        return;
      }
    }
    
    // Optimistic update
    const tempId = Date.now().toString();
    const newMessage = {
      id: tempId,
      thread_id: currentThread.id,
      user_id: user.id,
      content,
      role: 'user',
      created_at: new Date().toISOString(),
      metadata: {}
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    try {
      // Send message to API
      const response = await ChatService.sendMessage(currentThread.id, { content });
      
      // Update with response from server
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempId),
        response
      ]);
      
      // Add AI response (when it comes back)
      const aiResponse = await ChatService.getAIResponse(currentThread.id);
      setMessages(prev => [...prev, aiResponse]);
      
    } catch (err) {
      setError('Failed to send message');
      console.error(err);
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempId));
    }
  };
  
  return (
    <div className="flex h-full">
      <ChatSidebar threads={threads} activeThreadId={currentThread?.id} />
      
      <div className="flex-1 flex flex-col h-full">
        <ChatHeader 
          thread={currentThread}
          onCreateNewThread={() => navigate('/chat/new')}
        />
        
        <ChatMessageList messages={messages} isLoading={isLoading} />
        
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

export default ChatContainer;
```

#### 2. Chat Message Components

Components for displaying chat messages with Claude-style formatting:

```jsx
// src/components/chat/ChatMessage.jsx
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const isAI = message.role === 'assistant';
  const isUser = message.role === 'user';
  
  return (
    <div className={`py-6 ${isAI ? 'bg-gray-50' : 'bg-white'}`}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-start">
          {/* Avatar */}
          <div className="flex-shrink-0 mr-4">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm
              ${isAI ? 'bg-violet-100 text-violet-700' : 'bg-blue-100 text-blue-700'}
            `}>
              {isAI ? 'AI' : message.user_id.toString()[0]}
            </div>
          </div>
          
          {/* Message content */}
          <div className="flex-1 overflow-hidden">
            <div className="flex items-center mb-1">
              <h3 className="text-sm font-medium">
                {isAI ? 'Assistant' : 'You'}
              </h3>
              <span className="ml-2 text-xs text-gray-500">
                {new Date(message.created_at).toLocaleTimeString()}
              </span>
              
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="ml-auto text-xs text-gray-500 hover:text-gray-700"
              >
                {isExpanded ? 'Collapse' : 'Expand'}
              </button>
            </div>
            
            {isExpanded && (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
```

```jsx
// src/components/chat/ChatMessageList.jsx
import { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';

const ChatMessageList = ({ messages, isLoading }) => {
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map(message => (
        <ChatMessage key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="py-6 bg-gray-50">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <div className="flex-shrink-0 mr-4">
                <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center">
                  <span className="text-violet-700 text-sm">AI</span>
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center mb-1">
                  <h3 className="text-sm font-medium">Assistant</h3>
                </div>
                <div className="animate-pulse">
                  <div className="h-2 bg-slate-200 rounded w-3/4 mb-2"></div>
                  <div className="h-2 bg-slate-200 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessageList;
```

#### 3. Chat Input Component

```jsx
// src/components/chat/ChatInput.jsx
import { useState } from 'react';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };
  
  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="flex">
          <div className="flex-1">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message..."
              rows={1}
              className="block w-full px-4 py-2 border border-gray-300 rounded-l-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              disabled={disabled}
              style={{ resize: 'none' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  handleSubmit(e);
                }
              }}
            />
          </div>
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className={`
              px-4 py-2 border border-transparent rounded-r-md shadow-sm text-sm font-medium text-white
              ${disabled || !message.trim() 
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'}
            `}
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
};

export default ChatInput;
```

### Phase 3: Chat Services and API Integration

#### 1. Chat Service

```jsx
// src/services/ChatService.js
import axios from 'axios';
import { API_BASE_URL } from '../config';

const API_ENDPOINTS = {
  THREADS: `${API_BASE_URL}/api/chat/threads`,
  MESSAGES: (threadId) => `${API_BASE_URL}/api/chat/threads/${threadId}/messages`,
  THREAD: (threadId) => `${API_BASE_URL}/api/chat/threads/${threadId}`,
};

class ChatService {
  static async getThreads() {
    try {
      const response = await axios.get(API_ENDPOINTS.THREADS);
      return response.data;
    } catch (error) {
      console.error('Error fetching chat threads:', error);
      throw error;
    }
  }
  
  static async getThread(threadId) {
    try {
      const response = await axios.get(API_ENDPOINTS.THREAD(threadId));
      return response.data;
    } catch (error) {
      console.error(`Error fetching thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async createThread(threadData) {
    try {
      const response = await axios.post(API_ENDPOINTS.THREADS, threadData);
      return response.data;
    } catch (error) {
      console.error('Error creating chat thread:', error);
      throw error;
    }
  }
  
  static async sendMessage(threadId, messageData) {
    try {
      const response = await axios.post(API_ENDPOINTS.MESSAGES(threadId), messageData);
      return response.data;
    } catch (error) {
      console.error(`Error sending message to thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async getAIResponse(threadId) {
    // In a real implementation, this might use server-sent events or websockets
    // For now, we'll simulate a delay and then fetch the latest message
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      const response = await axios.get(API_ENDPOINTS.MESSAGES(threadId), {
        params: { 
          role: 'assistant',
          limit: 1,
          order: 'desc'
        }
      });
      
      return response.data[0];
    } catch (error) {
      console.error(`Error getting AI response for thread ${threadId}:`, error);
      throw error;
    }
  }
  
  static async deleteThread(threadId) {
    try {
      await axios.delete(API_ENDPOINTS.THREAD(threadId));
      return true;
    } catch (error) {
      console.error(`Error deleting thread ${threadId}:`, error);
      throw error;
    }
  }
}

export default ChatService;
```

### Phase 4: Route and Page Integration

#### 1. Update AppRoutes.jsx

Add the new chat routes to the existing AppRoutes:

```jsx
// src/components/common/AppRoutes.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../../pages/HomePage';
import LoginPage from '../../pages/LoginPage';
import RegisterPage from '../../pages/RegisterPage';
import DashboardPage from '../../pages/DashboardPage';
import ChatPage from '../../pages/ChatPage';
import VerifyEmailPage from '../../pages/VerifyEmailPage';
import ForgotPasswordPage from '../../pages/ForgotPasswordPage';
import ResetPasswordPage from '../../pages/ResetPasswordPage';
import OAuthCallback from '../../pages/auth/OAuthCallback';
import UnauthorizedPage from '../../pages/UnauthorizedPage';
import ProtectedRoute, { AdminRoute, SuperAdminRoute } from '../ProtectedRoute';
import AdminDashboard from '../../pages/admin/AdminDashboard';
import UserManagement from '../../pages/admin/UserManagement';
import SystemSettings from '../../pages/admin/SystemSettings';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      
      {/* Protected user routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } 
      />
      
      {/* Chat routes */}
      <Route 
        path="/chat" 
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/chat/:threadId" 
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } 
      />
      
      {/* Admin-only routes */}
      <Route 
        path="/admin" 
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        } 
      />
      {/* ... other admin routes ... */}
    </Routes>
  );
};

export default AppRoutes;
```

#### 2. Create Chat Page

```jsx
// src/pages/ChatPage.jsx
import DashboardLayout from '../components/layout/DashboardLayout';
import ChatContainer from '../components/chat/ChatContainer';

const ChatPage = () => {
  return (
    <DashboardLayout>
      <ChatContainer />
    </DashboardLayout>
  );
};

export default ChatPage;
```

#### 3. Update Dashboard Page

Refactor the existing Dashboard page to use the new DashboardLayout:

```jsx
// src/pages/DashboardPage.jsx
import DashboardLayout from '../components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import EmailVerificationStatus from '../components/auth/EmailVerificationStatus';
import ProfileView from '../components/profile/ProfileView';

const DashboardPage = () => {
  const { user, refreshUserData } = useAuth();
  
  useEffect(() => {
    refreshUserData();
  }, [refreshUserData]);

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>
        
        {!user?.is_email_verified && (
          <div className="mb-6">
            <EmailVerificationStatus />
          </div>
        )}
        
        <div className="bg-white shadow overflow-hidden sm:rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Welcome, {user?.full_name || user?.email}</h2>
          <p className="text-gray-600 mb-4">
            This is your personalized dashboard where you can manage your account and access various features.
          </p>
          
          {/* Dashboard cards/widgets would go here */}
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
            {/* Activity Summary Card */}
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-base font-medium text-gray-900">Recent Activity</h3>
                <div className="mt-3 text-sm text-gray-500">
                  <p>Last login: {new Date(user?.last_login || Date.now()).toLocaleString()}</p>
                </div>
              </div>
            </div>
            
            {/* Chat Summary Card */}
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-base font-medium text-gray-900">Chat</h3>
                <div className="mt-3 text-sm text-gray-500">
                  <p>Start a new conversation with our AI assistant</p>
                </div>
                <div className="mt-4">
                  <a
                    href="/chat"
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Go to Chat
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;
```

### Phase 5: Accessibility & Responsive Considerations

1. Ensure WCAG 2.1 AA compliance:
   - Adequate color contrast
   - Keyboard navigation support
   - Proper ARIA attributes
   - Screen reader compatibility

2. Implement responsive behavior:
   - Sidebar collapses on smaller screens
   - Context panel becomes a modal on mobile
   - Adjust typography and spacing for mobile devices

3. Add focus management for improved keyboard navigation

4. Implement responsive techniques:
   - Mobile-first approach
   - Use CSS Grid and Flexbox for layout
   - Media queries for targeted adjustments

## Required Dependencies

Update `package.json` to include these additional dependencies:

```json
{
  "dependencies": {
    "@headlessui/react": "^1.7.17",
    "react-markdown": "^8.0.7",
    "material-icons": "^1.13.12"
  }
}
```

## Implementation Timeline

1. **Week 1**: Core Layout Components
   - Create DashboardLayout, Sidebar, TopNavbar, and ContextPanel components
   - Update existing pages to use the new layout

2. **Week 2**: Chat Interface Components  
   - Implement ChatContainer, ChatMessage, ChatMessageList, and ChatInput components
   - Develop ChatService for API integration

3. **Week 3**: Route Integration and Testing
   - Update routes to include chat functionality
   - Test with backend API integration
   - Fix any issues with responsive design

4. **Week 4**: Refinement and Accessibility
   - Polish UI elements and transitions
   - Conduct accessibility audit and fix issues
   - Optimize performance

## Success Criteria

1. The UI follows Claude's minimalist aesthetic with the three-panel layout
2. Chat functionality is fully integrated with the backend API
3. The interface is responsive and works on mobile, tablet, and desktop
4. The application passes accessibility tests (WCAG 2.1 AA)
5. The UI is consistent across the entire application

## Conclusion

This implementation plan provides a comprehensive roadmap for refactoring the User Authentication System's frontend to create a professional Claude-style dashboard with minimal use of decorative elements and emojis. The design emphasizes functionality, accessibility, and a clean user experience while maintaining the core features of the application.