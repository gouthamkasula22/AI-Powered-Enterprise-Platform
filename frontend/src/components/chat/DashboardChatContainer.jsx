import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';

// Note: We'll use mock data for now
const mockThreads = [
  {
    id: 1,
    title: 'Getting Started',
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    metadata: {}
  },
  {
    id: 2,
    title: 'Help with Authentication',
    user_id: 1,
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    metadata: {}
  }
];

const mockMessages = [
  {
    id: 1,
    thread_id: 1,
    user_id: 1,
    content: 'Hello, how can I use this system?',
    role: 'user',
    created_at: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    metadata: {}
  },
  {
    id: 2,
    thread_id: 1,
    user_id: null,
    content: 'Welcome to the User Authentication System! This is a secure platform for managing user accounts, permissions, and authentication. How can I assist you today?',
    role: 'assistant',
    created_at: new Date(Date.now() - 270000).toISOString(), // 4.5 minutes ago
    metadata: {}
  }
];

const DashboardChatContainer = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [threads, setThreads] = useState(mockThreads);
  const [currentThread, setCurrentThread] = useState(null);
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Initialize with default thread when component mounts
  useEffect(() => {
    // Start with the first thread if available
    if (mockThreads.length > 0) {
      const defaultThread = mockThreads[0];
      setActiveThreadId(defaultThread.id);
      setCurrentThread(defaultThread);
      
      // Load messages for default thread
      const threadMessages = mockMessages.filter(m => m.thread_id === defaultThread.id);
      setMessages(threadMessages || []);
    }
  }, []);
  
  // Load messages when active thread changes
  useEffect(() => {
    if (!activeThreadId) return;
    
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const thread = mockThreads.find(t => t.id === activeThreadId);
      const threadMessages = mockMessages.filter(m => m.thread_id === activeThreadId);
      
      setCurrentThread(thread || null);
      setMessages(threadMessages || []);
      setIsLoading(false);
    }, 300); // Short delay for simulation
  }, [activeThreadId]);
  
  const handleSendMessage = async (content) => {
    // If no current thread, create one
    if (!currentThread) {
      // In a real implementation, this would be an API call
      const newThread = {
        id: mockThreads.length + 1,
        title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
        user_id: user?.id || 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
      };
      
      setThreads(prev => [newThread, ...prev]);
      setCurrentThread(newThread);
      setActiveThreadId(newThread.id);
      return;
    }
    
    // Optimistic update
    const tempId = Date.now().toString();
    const newMessage = {
      id: tempId,
      thread_id: currentThread.id,
      user_id: user?.id || 1,
      content,
      role: 'user',
      created_at: new Date().toISOString(),
      metadata: {}
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Simulate API call
    setIsLoading(true);
    
    // Simulate response delay
    setTimeout(() => {
      // Add AI response
      const aiResponse = {
        id: tempId + 1,
        thread_id: currentThread.id,
        user_id: null,
        content: `This is a simulated Claude-style assistant response to your question: "${content}"\n\nI'm here to help you with user authentication, security questions, and other related topics. What specific information are you looking for today?`,
        role: 'assistant',
        created_at: new Date().toISOString(),
        metadata: {}
      };
      
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };
  
  // Handle thread selection
  const handleThreadSelect = (threadId) => {
    setActiveThreadId(threadId);
  };
  
  // Create new thread
  const handleNewThread = () => {
    setCurrentThread(null);
    setActiveThreadId(null);
    setMessages([]);
  };
  
  return (
    <div className="flex h-full flex-col bg-white rounded-lg overflow-hidden border border-gray-200">
      <ChatHeader 
        thread={currentThread}
        onCreateNewThread={handleNewThread}
      />
      
      <div className="flex flex-1 h-[calc(100%-10rem)]">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatMessageList 
            messages={messages} 
            isLoading={isLoading} 
          />
        </div>
      </div>
      
      <div className="border-t border-gray-200 bg-white p-4">
        <ChatInput 
          onSendMessage={handleSendMessage} 
          disabled={isLoading} 
          placeholder="Message assistant..."
        />
      </div>
    </div>
  );
};

export default DashboardChatContainer;