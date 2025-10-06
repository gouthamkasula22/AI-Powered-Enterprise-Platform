import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';
import { generateImage, getTaskStatus } from '../../services/ImageService';
import ChatService from '../../services/ChatService';

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
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Load threads when component mounts
  useEffect(() => {
    const loadThreads = async () => {
      try {
        const fetchedThreads = await ChatService.getThreads();
        setThreads(fetchedThreads || []);
        
        // If no threadId in URL but we have threads, navigate to the first thread
        if (!threadId && fetchedThreads && fetchedThreads.length > 0) {
          navigate(`/chat/${fetchedThreads[0].id}`);
        }
      } catch (error) {
        console.error('Error loading threads:', error);
        setThreads([]);
        // Fallback to mock threads if API fails
        setThreads(mockThreads);
        if (!threadId && mockThreads.length > 0) {
          navigate(`/chat/${mockThreads[0].id}`);
        }
      }
    };
    
    loadThreads();
  }, [navigate, threadId]);
  
  // Load thread and messages when threadId changes
  useEffect(() => {
    const loadThread = async () => {
      if (!threadId || threadId === 'new') {
        setCurrentThread(null);
        setMessages([]);
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      
      try {
        const thread = await ChatService.getThread(threadId);
        const messages = await ChatService.getMessages(threadId);
        
        setCurrentThread(thread);
        setMessages(messages || []);
      } catch (error) {
        console.error('Error loading thread:', error);
        setCurrentThread(null);
        setMessages([]);
        // You might want to show an error toast or redirect
      } finally {
        setIsLoading(false);
      }
    };
    
    loadThread();
  }, [threadId]);
  
  const handleSendMessage = async (content, chatMode = 'general') => {
    try {
      // If no current thread or "new" thread, create one
      if (!currentThread || threadId === 'new') {
        const threadData = {
          title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
          metadata: { chatMode }
        };
        
        const newThread = await ChatService.createThread(threadData);
        setThreads(prev => [newThread, ...prev]);
        setCurrentThread(newThread);
        navigate(`/chat/${newThread.id}`);
        
        // Send the first message to the new thread
        await ChatService.sendMessage(newThread.id, {
          content,
          role: 'user',
          metadata: { chatMode }
        });
        
        // Refresh messages for the new thread
        const messages = await ChatService.getMessages(newThread.id);
        setMessages(messages);
        return;
      }
      
      // Optimistic update for existing thread
      const tempId = Date.now().toString();
      const newMessage = {
        id: tempId,
        thread_id: currentThread.id,
        user_id: user.id,
        content,
        role: 'user',
        created_at: new Date().toISOString(),
        metadata: { chatMode }
      };
      
      setMessages(prev => [...prev, newMessage]);
      setIsLoading(true);
      
      // Send message to backend
      const response = await ChatService.sendMessage(currentThread.id, {
        content,
        role: 'user',
        metadata: { chatMode }
      });
      
      // The backend should return both the user message and AI response
      // Replace the optimistic message with the real one and add AI response
      if (response.messages) {
        setMessages(prev => {
          // Remove the optimistic message and add the real messages
          const withoutOptimistic = prev.filter(msg => msg.id !== tempId);
          return [...withoutOptimistic, ...response.messages];
        });
      }
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      // Remove optimistic message on error
      setMessages(prev => prev.filter(msg => msg.id !== tempId));
      // You might want to show an error toast here
    }
  };

  const handleImageCommand = async (imagePrompt) => {
    if (!currentThread || threadId === 'new') {
      alert('Please start a conversation first before generating images');
      return;
    }

    // Don't add user message here - it should be handled by the regular sendMessage flow

    // Add loading message
    const tempLoadingId = (Date.now() + 1).toString();
    const loadingMessage = {
      id: tempLoadingId,
      thread_id: currentThread.id,
      user_id: null,
      content: `🎨 Generating image: "${imagePrompt}"...\n\nThis may take 10-30 seconds.`,
      role: 'assistant',
      created_at: new Date().toISOString(),
      metadata: { isImageLoading: true }
    };

    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Start image generation
      const task = await generateImage({
        prompt: imagePrompt,
        thread_id: currentThread.id
      });

      // Poll for completion
      const pollProgress = setInterval(async () => {
        try {
          const status = await getTaskStatus(task.task_id);
          
          if (status.status === 'completed') {
            clearInterval(pollProgress);
            
            // Remove loading message and add image message
            setMessages(prev => {
              const filtered = prev.filter(msg => msg.id !== tempLoadingId);
              return [...filtered, {
                id: (Date.now() + 2).toString(),
                thread_id: currentThread.id,
                user_id: null,
                content: '', // Remove success text, just show the image
                role: 'assistant',
                created_at: new Date().toISOString(),
                generated_image: status.image_data,
                metadata: {}
              }];
            });
            
          } else if (status.status === 'failed') {
            clearInterval(pollProgress);
            
            // Replace loading message with error
            setMessages(prev => prev.map(msg => 
              msg.id === tempLoadingId 
                ? {
                    ...msg,
                    content: `❌ Image generation failed: ${status.error || 'Unknown error'}`,
                    metadata: {}
                  }
                : msg
            ));
          }
        } catch (err) {
          console.error('Error checking task status:', err);
        }
      }, 2000);

      // Cleanup after 5 minutes
      setTimeout(() => {
        clearInterval(pollProgress);
      }, 300000);

    } catch (error) {
      // Replace loading message with error
      setMessages(prev => prev.map(msg => 
        msg.id === tempLoadingId 
          ? {
              ...msg,
              content: `❌ Failed to start image generation: ${error.message}`,
              metadata: {}
            }
          : msg
      ));
      console.error('Image generation failed:', error);
    }
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
        <ChatInput 
          onSendMessage={handleSendMessage} 
          onImageCommand={handleImageCommand}
          disabled={isLoading} 
          placeholder="Message Assistant..." 
        />
      </div>
    </div>
  );
};

export default ChatContainer;