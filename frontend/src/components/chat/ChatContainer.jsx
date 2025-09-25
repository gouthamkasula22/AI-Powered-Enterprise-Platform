import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';

// Note: We'll need to create this service later
// For now, we'll use mock data
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

const ChatContainer = () => {
  const { threadId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [threads, setThreads] = useState(mockThreads);
  const [currentThread, setCurrentThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // "Fetch" threads when component mounts
  useEffect(() => {
    // In a real implementation, this would be an API call
    setThreads(mockThreads);
    
    // If no threadId in URL but we have threads, navigate to the first thread
    if (!threadId && mockThreads.length > 0) {
      navigate(`/chat/${mockThreads[0].id}`);
    }
  }, [navigate, threadId]);
  
  // "Fetch" messages when threadId changes
  useEffect(() => {
    if (!threadId || threadId === 'new') return;
    
    const numericThreadId = parseInt(threadId, 10);
    setIsLoading(true);
    
    // In a real implementation, this would be an API call
    setTimeout(() => {
      const thread = mockThreads.find(t => t.id === numericThreadId);
      const threadMessages = mockMessages.filter(m => m.thread_id === numericThreadId);
      
      setCurrentThread(thread || null);
      setMessages(threadMessages || []);
      setIsLoading(false);
    }, 500); // Simulate network delay
  }, [threadId]);
  
  const handleSendMessage = async (content) => {
    // If no current thread or "new" thread, create one
    if (!currentThread || threadId === 'new') {
      // In a real implementation, this would be an API call
      const newThread = {
        id: mockThreads.length + 1,
        title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
        user_id: user.id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
      };
      
      setThreads(prev => [newThread, ...prev]);
      setCurrentThread(newThread);
      navigate(`/chat/${newThread.id}`);
      return;
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
    
    // Simulate API call
    setIsLoading(true);
    
    // Simulate response delay
    setTimeout(() => {
      // Add AI response
      const aiResponse = {
        id: tempId + 1,
        thread_id: currentThread.id,
        user_id: null,
        content: `This is a mock response to: "${content}"`,
        role: 'assistant',
        created_at: new Date().toISOString(),
        metadata: {}
      };
      
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };
  
  return (
    <div className="flex h-full flex-col bg-white rounded-lg overflow-hidden border border-gray-200">
      <ChatHeader 
        thread={currentThread}
        onCreateNewThread={() => navigate('/chat/new')}
      />
      
      <div className="flex flex-1 h-[calc(100%-10rem)]">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatMessageList messages={messages} isLoading={isLoading} />
        </div>
      </div>
      
      <div className="border-t border-gray-200 bg-white">
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} placeholder="Message Assistant..." />
      </div>
    </div>
  );
};

export default ChatContainer;