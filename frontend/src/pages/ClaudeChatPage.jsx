import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import ClaudeLayout from '../components/layout/ClaudeLayout';
import axios from 'axios';

// Import MockAuthContext for development if needed
// import { useMockAuth } from '../contexts/MockAuthContext';

const ClaudeChatPage = () => {
  const { user, token } = useAuth();
  const { isDarkMode } = useTheme();
  const { threadId } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatTitle, setChatTitle] = useState('');
  const [error, setError] = useState(null);
  const [chatMode, setChatMode] = useState('general');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Function to load chat data based on threadId
  const fetchConversation = async () => {
    if (!token) return;
    
    setError(null); // Clear any previous errors
    try {
      if (threadId && threadId !== 'new') {
        setIsLoading(true);
        // Fetch conversation details
        const conversationResponse = await axios.get(`/api/conversations/${threadId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setChatTitle(conversationResponse.data.title);
        
        // Fetch messages for the conversation
        const messagesResponse = await axios.get(`/api/conversations/${threadId}/messages`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Transform API messages to our format, with error handling
        const messagesData = messagesResponse.data.messages || [];
        const formattedMessages = messagesData.map(msg => ({
          id: msg.id,
          content: msg.content || '',
          role: msg.role === 'user' ? 'user' : 'assistant',
          timestamp: msg.created_at || new Date().toISOString()
        }));
        
        setMessages(formattedMessages);
      } else {
        // New chat
        setChatTitle('');
        setMessages([]);
      }
    } catch (err) {
      console.error('Error fetching conversation:', err);
      
      // Show different error messages based on the error type
      if (err.response) {
        // Server responded with an error status
        if (err.response.status === 404) {
          setError('This conversation could not be found. It may have been deleted.');
        } else if (err.response.status === 401 || err.response.status === 403) {
          setError('You do not have permission to view this conversation.');
        } else {
          setError(`Could not load conversation (Error: ${err.response.status})`);
        }
      } else if (err.request) {
        // No response received
        setError('Network error: Could not reach server');
      } else {
        setError('Failed to load conversation');
      }
      
      // If API isn't available, fall back to mock data in development mode
      if (process.env.NODE_ENV === 'development' && threadId && threadId !== 'new') {
        setChatTitle(`Chat Thread #${threadId}`);
        
        // Fallback to mock messages
        const mockMessages = [
          {
            id: 101,
            content: "How can I implement secure user authentication in my application?",
            role: 'user',
            timestamp: new Date(Date.now() - 3600000).toISOString()
          },
          {
            id: 102,
            content: "To implement secure user authentication, I recommend using industry standard practices like:\n\n1. Password hashing with bcrypt or Argon2\n2. HTTPS for all communications\n3. Multi-factor authentication\n4. CSRF protection\n5. Rate limiting to prevent brute force attacks\n6. JWT or session-based authentication\n\nWould you like me to elaborate on any of these approaches?",
            role: 'assistant',
            timestamp: new Date(Date.now() - 3500000).toISOString()
          }
        ];
        
        setMessages(mockMessages);
      }
    } finally {
      setIsLoading(false);
    }
  };
    
  // Load chat data when threadId or token changes
  useEffect(() => {
    fetchConversation();
  }, [threadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Function to handle sending messages
  const handleSendMessage = async (e) => {
    console.log('sendMessage called with:', message);
    console.log('token:', !!token, 'isLoading:', isLoading, 'message.trim():', !!message.trim());
    
    e.preventDefault();
    if (!message.trim() || isLoading || !token) {
      console.log('Early return - conditions not met');
      return;
    }
    
    // Add user message to UI immediately for better UX
    const userMessage = {
      id: `temp-${Date.now()}`,
      content: message,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const messageContent = message;
    setMessage('');
    setIsLoading(true);
    
    try {
      // For new chat, create a conversation first
      if (!threadId || threadId === 'new') {
        // Derive chat title from first message (truncated)
        const newTitle = messageContent.length > 30 ? messageContent.substring(0, 30) + '...' : messageContent;
        
        try {
          console.log('Making API call to create conversation');
          // Create new conversation
          const conversationResponse = await axios.post('/api/conversations', {
            title: newTitle,
            category: 'general'
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          console.log('Conversation created:', conversationResponse.data);
          
          const newThreadId = conversationResponse.data.id;
          setChatTitle(newTitle);
          
          // Send first message
          const messageResponse = await axios.post(`/api/conversations/${newThreadId}/messages`, {
            content: messageContent,
            chat_mode: chatMode
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          // Update URL without reload
          navigate(`/chat/${newThreadId}`, { replace: true });
          
          // The message response should already include the AI's response
          // If not, we need to fetch messages again
          let aiMessage;
          
          // First check if messageResponse already includes AI response
          if (messageResponse.data && messageResponse.data.ai_response) {
            aiMessage = {
              id: messageResponse.data.ai_response.id,
              content: messageResponse.data.ai_response.content,
              role: 'assistant',
              timestamp: messageResponse.data.ai_response.created_at
            };
          } else {
            // Otherwise, fetch all messages and get the latest one
            const messagesResponse = await axios.get(`/api/conversations/${newThreadId}/messages`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            
            const messages = messagesResponse.data.messages;
            if (messages && messages.length > 1) {
              // Assume the last message is the AI response
              const lastMessage = messages[messages.length - 1];
              if (lastMessage.role === 'assistant') {
                aiMessage = {
                  id: lastMessage.id,
                  content: lastMessage.content,
                  role: 'assistant',
                  timestamp: lastMessage.created_at
                };
              }
            }
          }
          
          if (aiMessage) {
            setMessages(prev => [...prev.slice(0, -1), 
              // Replace temp user message with real one
              {
                id: messageResponse.data.id,
                content: messageResponse.data.content,
                role: 'user',
                timestamp: messageResponse.data.created_at
              },
              aiMessage
            ]);
          }
        } catch (err) {
          console.error('Error creating conversation:', err);
          
          // Fallback to mock response if API fails
          setTimeout(() => {
            const aiMessage = {
              id: Date.now() + 1,
              content: `This is a simulated response to: "${messageContent}"`,
              role: 'assistant',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, aiMessage]);
          }, 1500);
        }
      } else {
        // Existing conversation
        try {
          console.log('Making API call to send message to existing conversation');
          // Send message to existing conversation
          const messageResponse = await axios.post(`/api/conversations/${threadId}/messages`, {
            content: messageContent,
            chat_mode: chatMode
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          console.log('Message sent:', messageResponse.data);
          
          // Similar approach as with new conversations
          let aiMessage;
          
          // First check if messageResponse already includes AI response
          if (messageResponse.data && messageResponse.data.ai_response) {
            aiMessage = {
              id: messageResponse.data.ai_response.id,
              content: messageResponse.data.ai_response.content,
              role: 'assistant',
              timestamp: messageResponse.data.ai_response.created_at
            };
          } else {
            // Otherwise, fetch all messages and get the latest one
            const messagesResponse = await axios.get(`/api/conversations/${threadId}/messages`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            
            const messages = messagesResponse.data.messages;
            if (messages && messages.length > 0) {
              // Find the latest assistant message
              const assistantMessages = messages.filter(msg => msg.role === 'assistant');
              if (assistantMessages.length > 0) {
                const lastMessage = assistantMessages[assistantMessages.length - 1];
                aiMessage = {
                  id: lastMessage.id,
                  content: lastMessage.content,
                  role: 'assistant',
                  timestamp: lastMessage.created_at
                };
              }
            }
          }
          
          if (aiMessage) {
            
            setMessages(prev => [...prev.slice(0, -1), 
              // Replace temp user message with real one
              {
                id: messageResponse.data.id,
                content: messageResponse.data.content,
                role: 'user',
                timestamp: messageResponse.data.created_at
              },
              aiMessage
            ]);
          }
        } catch (err) {
          console.error('Error sending message:', err);
          
          // Fallback to mock response if API fails
          setTimeout(() => {
            const aiMessage = {
              id: Date.now() + 1,
              content: `This is a simulated response to: "${messageContent}"`,
              role: 'assistant',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, aiMessage]);
          }, 1500);
        }
      }
    } catch (err) {
      console.error('Error in message handling:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // File handling functions for admin users
  const handleFileSelect = (event) => {
    setSelectedFiles(Array.from(event.target.files));
  };

  const handleUploadDocuments = async () => {
    if (selectedFiles.length === 0) return;
    
    setUploading(true);
    
    try {
      // Create a form data for each file (the endpoint expects one file at a time)
      const uploadPromises = selectedFiles.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        // Only include thread_id if we have a valid current thread
        if (threadId && threadId !== 'new') {
          const numericThreadId = parseInt(threadId, 10);
          formData.append('thread_id', numericThreadId.toString());
        }
        // If no thread_id, let the backend create/find an appropriate thread
        
        return await axios.post('/api/v1/documents/upload', formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      });
      
      await Promise.all(uploadPromises);
      
      setShowUploadModal(false);
      setSelectedFiles([]);
      alert('Documents uploaded successfully!');
    } catch (error) {
      console.error('Upload error:', error);
      let errorMessage = 'Failed to upload documents';
      
      if (error.response?.data?.detail) {
        // Handle string or array of error details
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map(err => err.msg || err).join(', ');
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <ClaudeLayout>
      <div className="flex flex-col h-full">
        {/* Chat Title Bar - Only show when chat has messages */}
        {messages.length > 0 && chatTitle && (
          <div className="border-b border-gray-800 p-2 px-4">
            <h2 className="text-lg font-medium text-gray-200">{chatTitle}</h2>
          </div>
        )}
        
        {/* Welcome Header - Only show when no messages */}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center pt-20 pb-12">
            <div className="text-orange-400 text-4xl mb-2">✧</div>
            <h1 className={`text-4xl font-light ${isDarkMode ? 'text-gray-100' : 'text-gray-900'} mb-6`}>Welcome to Chat Assistant</h1>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'} text-center max-w-md mb-8`}>
              I'm here to help with your questions about user authentication, security, and account management.
            </p>
            <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
              <button className={`px-3 py-2 ${isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'} rounded-md text-sm flex items-center`}>
                Help with authentication flows
              </button>
              <button className={`px-3 py-2 ${isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'} rounded-md text-sm flex items-center`}>
                Explain password security
              </button>
              <button className={`px-3 py-2 ${isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'} rounded-md text-sm flex items-center`}>
                Review my account settings
              </button>
              <button className={`px-3 py-2 ${isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'} rounded-md text-sm flex items-center`}>
                Help with access control
              </button>
            </div>
          </div>
        )}
        
        {/* Chat Messages Area */}
        <div className={`flex-1 overflow-y-auto px-4 pb-4 ${messages.length > 0 ? 'pt-4' : ''}`}>
          <div className="max-w-3xl mx-auto">
            {messages.map(msg => (
              <div 
                key={msg.id} 
                className={`py-6 ${msg.role === 'assistant' ? 'bg-gray-800/20 rounded-md' : ''} mb-4`}
              >
                <div className="max-w-3xl mx-auto px-4">
                  <div className="flex items-center mb-3">
                    <div className={`w-6 h-6 rounded-full ${msg.role === 'assistant' ? 'bg-orange-500/20 text-orange-500' : 'bg-gray-700'} flex items-center justify-center text-sm mr-2`}>
                      {msg.role === 'assistant' ? 'C' : user?.name?.charAt(0) || 'U'}
                    </div>
                    <h3 className="text-sm font-medium text-gray-400">
                      {msg.role === 'assistant' ? 'Claude' : 'You'}
                    </h3>
                  </div>
                  <div className="text-gray-100 whitespace-pre-wrap pl-8">
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="py-6 mb-4">
                <div className="max-w-3xl mx-auto px-4">
                  <div className="flex items-center mb-3">
                    <div className="w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-sm mr-2">
                      C
                    </div>
                    <h3 className="text-sm font-medium text-gray-400">Claude</h3>
                  </div>
                  <div className="animate-pulse pl-8">
                    <div className="h-2 bg-gray-700 rounded w-3/4 mb-2"></div>
                    <div className="h-2 bg-gray-700 rounded w-1/2 mb-2"></div>
                    <div className="h-2 bg-gray-700 rounded w-2/3"></div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Error message */}
            {error && (
              <div className="py-6 mb-4">
                <div className="max-w-3xl mx-auto px-4">
                  <div className="rounded-md bg-red-900/20 border border-red-800/30 p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-500 flex items-center justify-center text-sm mr-2">
                        !
                      </div>
                      <h3 className="text-sm font-medium text-red-400">Error</h3>
                    </div>
                    <p className="text-sm text-gray-300 pl-8">{error}</p>
                    <div className="mt-3 pl-8">
                      <button 
                        onClick={() => {
                          setError(null);
                          if (threadId && threadId !== 'new') {
                            fetchConversation();
                          }
                        }}
                        className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-gray-300"
                      >
                        Try Again
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Input Area */}
        <div className={`border-t ${isDarkMode ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'} p-4 relative`}>
          <div className="max-w-3xl mx-auto w-full">
            {/* Chat Mode Selector */}
            <div className="flex items-center mb-3">
              <label className={`text-sm font-medium mr-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Chat Mode:
              </label>
              <div className={`flex rounded-md p-1 ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
                <button
                  type="button"
                  onClick={() => setChatMode('general')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    chatMode === 'general'
                      ? isDarkMode 
                        ? 'bg-gray-700 text-blue-400 shadow-sm'
                        : 'bg-white text-blue-600 shadow-sm'
                      : isDarkMode
                        ? 'text-gray-400 hover:text-gray-200'
                        : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  General Chat
                </button>
                {user?.role?.toLowerCase() === 'admin' && (
                  <button
                    type="button"
                    onClick={() => setChatMode('rag')}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      chatMode === 'rag'
                        ? isDarkMode 
                          ? 'bg-gray-700 text-blue-400 shadow-sm'
                          : 'bg-white text-blue-600 shadow-sm'
                        : isDarkMode
                          ? 'text-gray-400 hover:text-gray-200'
                          : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Document-Based
                  </button>
                )}
              </div>
              <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {chatMode === 'general' 
                  ? 'Chat with AI about anything' 
                  : 'Chat based on uploaded documents (Admin only)'
                }
              </p>
            </div>

            {/* Admin Tools - Only visible to admins */}
            {user?.role?.toLowerCase() === 'admin' && (
              <div className={`mb-4 p-4 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
                <h3 className={`font-medium mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Admin Tools</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                  >
                    Upload Documents
                  </button>
                  <button
                    onClick={() => setShowDocumentManager(true)}
                    className="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm"
                  >
                    Manage Documents
                  </button>
                </div>
              </div>
            )}
            <form onSubmit={handleSendMessage} className="flex flex-col relative">
              <div className="relative rounded-md shadow-sm mb-2">
                <textarea
                  rows={1}
                  value={message}
                  onChange={(e) => {
                    console.log('Input changed:', e.target.value);
                    setMessage(e.target.value);
                  }}
                  placeholder={chatMode === 'general' ? "Ask me anything..." : "Ask about your documents..."}
                  className={`block w-full rounded-lg py-3 px-4 ${
                    isDarkMode 
                      ? 'bg-gray-800 text-gray-100 focus:ring-gray-500 border-gray-700' 
                      : 'bg-gray-100 text-gray-900 focus:ring-blue-500 border-gray-300'
                  } focus:outline-none focus:ring-1 border resize-none`}
                  style={{ minHeight: '56px' }}
                  onKeyDown={(e) => {
                    console.log('Key pressed:', e.key, 'Shift:', e.shiftKey, 'Message:', message);
                    if (e.key === 'Enter' && !e.shiftKey) {
                      console.log('Enter key pressed, calling handleSendMessage');
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
                <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                  <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading}
                    className={`p-1 rounded-md ${!message.trim() || isLoading ? 'text-gray-600' : 'text-orange-400 hover:text-orange-500'}`}
                    onClick={(e) => {
                      console.log('Send button clicked');
                      handleSendMessage(e);
                    }}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z"></path>
                      <path d="M9 17l8-5-8-5z"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-gray-500">
                <div>
                  <span>Claude can make mistakes. Consider checking important information.</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="hover:text-gray-300">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
          
        {/* Quick actions - only show if messages empty */}
        {messages.length === 0 && (
          <div className="bg-black py-4">
            <div className="max-w-3xl mx-auto w-full">
              <div className="flex flex-wrap gap-2 justify-center">
                <button className="px-3 py-1.5 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded text-sm text-gray-300">
                  <span className="mr-2">🔐</span>Secure password tips
                </button>
                <button className="px-3 py-1.5 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded text-sm text-gray-300">
                  <span className="mr-2">🔄</span>Two-factor authentication help
                </button>
                <button className="px-3 py-1.5 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded text-sm text-gray-300">
                  <span className="mr-2">�</span>How to update my profile
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Document Upload Modal - Only for admins */}
      {showUploadModal && user?.role?.toLowerCase() === 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`p-6 rounded-lg max-w-md w-full mx-4 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Upload Documents
            </h3>
            <div className="mb-4">
              <input
                type="file"
                multiple
                accept=".pdf,.txt,.md,.doc,.docx"
                onChange={handleFileSelect}
                className={`w-full p-2 rounded border ${
                  isDarkMode 
                    ? 'bg-gray-700 text-white border-gray-600' 
                    : 'bg-white text-gray-900 border-gray-300'
                }`}
              />
              {selectedFiles.length > 0 && (
                <div className={`mt-2 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Selected: {selectedFiles.map(f => f.name).join(', ')}
                </div>
              )}
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setSelectedFiles([]);
                }}
                className={`px-4 py-2 rounded transition-colors ${
                  isDarkMode 
                    ? 'bg-gray-600 text-white hover:bg-gray-700' 
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleUploadDocuments}
                disabled={selectedFiles.length === 0 || uploading}
                className={`px-4 py-2 rounded transition-colors ${
                  selectedFiles.length === 0 || uploading
                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ClaudeLayout>
  );
};

export default ClaudeChatPage;