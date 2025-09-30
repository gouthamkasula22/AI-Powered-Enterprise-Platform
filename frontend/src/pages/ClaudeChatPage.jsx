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
  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gemini'); // Default to Gemini

  // Function to fetch user's documents
  const fetchDocuments = async () => {
    if (!token || !user || user.role.toLowerCase() !== 'admin') return;
    
    setLoadingDocuments(true);
    try {
      const response = await axios.get('/api/v1/documents/my-documents', {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Extract documents array from the response
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      alert('Failed to load documents');
    } finally {
      setLoadingDocuments(false);
    }
  };

  // Function to delete a document
  const deleteDocument = async (documentId) => {
    if (!token || !user || user.role.toLowerCase() !== 'admin') return;
    
    try {
      await axios.delete(`/api/v1/documents/${documentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Remove document from state
      setDocuments(documents.filter(doc => doc.id !== documentId));
      alert('Document deleted successfully');
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Failed to delete document');
    }
  };

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

  // Fetch documents for admin users on mount and when user changes
  useEffect(() => {
    if (user?.role?.toLowerCase() === 'admin' && token && documents.length === 0) {
      fetchDocuments();
    }
  }, [user, token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch documents when document manager is opened (refresh in case of new uploads)
  useEffect(() => {
    if (showDocumentManager && user?.role?.toLowerCase() === 'admin') {
      fetchDocuments();
    }
  }, [showDocumentManager]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch documents when document selector is opened (refresh in case of new uploads)
  useEffect(() => {
    if (showDocumentSelector && user?.role?.toLowerCase() === 'admin') {
      fetchDocuments();
    }
  }, [showDocumentSelector]); // eslint-disable-line react-hooks/exhaustive-deps

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
          // Automatically use RAG mode if documents are selected
          const effectiveChatMode = selectedDocuments.length > 0 ? 'rag' : chatMode;
          
          const messagePayload = {
            content: messageContent,
            chat_mode: effectiveChatMode,
            selected_documents: selectedDocuments.map(doc => doc.id),
            model: selectedModel
          };
          console.log('🔍 DEBUG: Message payload being sent:', JSON.stringify(messagePayload, null, 2));
          console.log('🔍 DEBUG: Selected documents before mapping:', selectedDocuments);
          console.log('🔍 DEBUG: Selected document IDs:', selectedDocuments.map(doc => doc.id));
          console.log('🔍 DEBUG: Effective chat mode:', messagePayload.chat_mode);
          
          // Use LangChain endpoint when documents are selected for better RAG processing
          const endpoint = selectedDocuments.length > 0 
            ? `/api/conversations/${newThreadId}/messages/langchain`
            : `/api/conversations/${newThreadId}/messages`;
          console.log('🔍 DEBUG: Using endpoint:', endpoint);
          
          const messageResponse = await axios.post(endpoint, messagePayload, {
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
              // Replace temp user message with real one - preserve original user content
              {
                id: messageResponse.data.id,
                content: messageContent, // Use the original user message content
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
          
          // Automatically use RAG mode if documents are selected
          const effectiveChatMode = selectedDocuments.length > 0 ? 'rag' : chatMode;
          
          const messagePayload = {
            content: messageContent,
            chat_mode: effectiveChatMode,
            selected_documents: selectedDocuments.map(doc => doc.id),
            model: selectedModel
          };
          console.log('🔍 DEBUG: Existing conversation payload:', JSON.stringify(messagePayload, null, 2));
          console.log('🔍 DEBUG: Selected documents for existing:', selectedDocuments);
          
          // Use LangChain endpoint when documents are selected for better RAG processing
          const endpoint = selectedDocuments.length > 0 
            ? `/api/conversations/${threadId}/messages/langchain`
            : `/api/conversations/${threadId}/messages`;
          console.log('🔍 DEBUG: Using endpoint for existing conversation:', endpoint);
          
          // Send message to existing conversation
          const messageResponse = await axios.post(endpoint, messagePayload, {
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
              // Replace temp user message with real one - preserve original user content
              {
                id: messageResponse.data.id,
                content: messageContent, // Use the original user message content
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
          <div className="flex flex-col items-center justify-center pt-24 pb-16">
            <div className="text-orange-400 text-6xl mb-4">✧</div>
            <h1 className={`text-5xl font-light ${isDarkMode ? 'text-gray-100' : 'text-gray-900'} mb-6`}>
              Intelligent Chat Assistant
            </h1>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'} text-center max-w-lg text-lg leading-relaxed`}>
              Start a conversation or upload documents to get contextual, intelligent responses powered by advanced AI.
            </p>
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
                    <div className={`w-6 h-6 rounded-full ${msg.role === 'assistant' ? (selectedModel === 'claude' ? 'bg-orange-500/20 text-orange-500' : 'bg-blue-500/20 text-blue-500') : 'bg-gray-700'} flex items-center justify-center text-sm mr-2`}>
                      {msg.role === 'assistant' ? (selectedModel === 'claude' ? 'C' : 'G') : user?.name?.charAt(0) || 'U'}
                    </div>
                    <h3 className="text-sm font-medium text-gray-400">
                      {msg.role === 'assistant' ? (selectedModel === 'claude' ? 'Claude' : 'Gemini') : 'You'}
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
                    <div className={`w-6 h-6 rounded-full ${selectedModel === 'claude' ? 'bg-orange-500/20 text-orange-500' : 'bg-blue-500/20 text-blue-500'} flex items-center justify-center text-sm mr-2`}>
                      {selectedModel === 'claude' ? 'C' : 'G'}
                    </div>
                    <h3 className="text-sm font-medium text-gray-400">{selectedModel === 'claude' ? 'Claude' : 'Gemini'}</h3>
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
              <div className={`mb-6 p-5 rounded-xl border ${isDarkMode ? 'bg-gray-800/50 border-gray-700/50 backdrop-blur-sm' : 'bg-gray-50/80 border-gray-200/50 backdrop-blur-sm'}`}>
                <div className="flex items-center mb-3">
                  <div className="w-2 h-2 bg-orange-400 rounded-full mr-2"></div>
                  <h3 className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>Document Management</h3>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 text-sm font-medium shadow-sm hover:shadow-md flex items-center justify-center"
                  >
                    Upload
                  </button>
                  <button
                    onClick={() => setShowDocumentManager(true)}
                    className="px-4 py-2.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all duration-200 text-sm font-medium shadow-sm hover:shadow-md flex items-center justify-center"
                  >
                    Manage
                  </button>
                  <button
                    onClick={() => setShowDocumentSelector(true)}
                    className={`px-4 py-2.5 ${selectedDocuments.length > 0 ? 'bg-green-600 hover:bg-green-700' : 'bg-orange-600 hover:bg-orange-700'} text-white rounded-lg transition-all duration-200 text-sm font-medium shadow-sm hover:shadow-md flex items-center justify-center`}
                  >
                    Select {selectedDocuments.length > 0 ? `(${selectedDocuments.length})` : ''}
                  </button>
                </div>
              </div>
            )}

            {/* Selected Documents Display */}
            {selectedDocuments.length > 0 && (
              <div className={`mb-4 p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-blue-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-sm font-medium ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                    Selected Documents ({selectedDocuments.length}):
                  </span>
                  <button
                    onClick={() => setSelectedDocuments([])}
                    className={`text-xs px-2 py-1 rounded ${isDarkMode ? 'bg-gray-600 text-white hover:bg-gray-500' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                  >
                    Clear All
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                        isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      <span>{doc.filename}</span>
                      <button
                        onClick={() => setSelectedDocuments(prev => prev.filter(d => d.id !== doc.id))}
                        className="text-xs opacity-70 hover:opacity-100"
                      >
                        ×
                      </button>
                    </div>
                  ))}
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
                  placeholder={
                    selectedDocuments.length > 0 
                      ? `Ask about your ${selectedDocuments.length} selected document${selectedDocuments.length > 1 ? 's' : ''}...` 
                      : "Start a conversation..."
                  }
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
              
              {/* Model Selector */}
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center space-x-2">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className={`text-sm px-3 py-1.5 rounded-lg border ${
                      isDarkMode 
                        ? 'bg-gray-800 border-gray-700 text-gray-300 focus:border-orange-500' 
                        : 'bg-white border-gray-300 text-gray-700 focus:border-blue-500'
                    } focus:outline-none focus:ring-1 transition-colors`}
                  >
                    <option value="claude">Claude Sonnet 3.5</option>
                    <option value="gemini">Gemini Pro</option>
                  </select>
                  <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    AI Model
                  </span>
                </div>
                {selectedDocuments.length > 0 && (
                  <div className={`text-xs ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>
                    📎 {selectedDocuments.length} document{selectedDocuments.length > 1 ? 's' : ''} selected
                  </div>
                )}
              </div>
              
              <div className="flex justify-between items-center text-xs text-gray-500">
                <div>
                  <span>{selectedModel === 'claude' ? 'Claude' : 'Gemini'} can make mistakes. Consider checking important information.</span>
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

      {/* Document Manager Modal - Only for admins */}
      {showDocumentManager && user?.role?.toLowerCase() === 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="flex justify-between items-center mb-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Manage Documents
              </h3>
              <button
                onClick={() => setShowDocumentManager(false)}
                className={`text-2xl font-bold hover:opacity-70 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}
              >
                ×
              </button>
            </div>
            
            {loadingDocuments ? (
              <div className={`text-center py-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div className={`text-center py-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                <div className="text-4xl mb-4">📄</div>
                <p className="text-lg mb-2">No documents uploaded yet</p>
                <p className="text-sm">Upload documents to get started with document-based chat</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div key={doc.id} className={`p-4 rounded-lg border ${
                    isDarkMode 
                      ? 'bg-gray-700 border-gray-600' 
                      : 'bg-gray-50 border-gray-200'
                  }`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                          {doc.filename}
                        </h4>
                        <div className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          <div>Size: {doc.size_bytes ? Math.round(doc.size_bytes / 1024) + ' KB' : 'Unknown'}</div>
                          <div>Type: {doc.file_type || 'Unknown'}</div>
                          <div>Words: {doc.word_count || 'Unknown'}</div>
                          <div>Uploaded: {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown'}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          if (window.confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
                            deleteDocument(doc.id);
                          }
                        }}
                        className="ml-4 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(true);
                  setShowDocumentManager(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Upload New Document
              </button>
              <button
                onClick={() => setShowDocumentManager(false)}
                className={`px-4 py-2 rounded transition-colors ${
                  isDarkMode 
                    ? 'bg-gray-600 text-white hover:bg-gray-700' 
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                }`}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Selector Modal - Only for admins */}
      {showDocumentSelector && user?.role?.toLowerCase() === 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`p-6 rounded-lg max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="flex justify-between items-center mb-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Select Documents for Context
              </h3>
              <button
                onClick={() => setShowDocumentSelector(false)}
                className={`text-2xl font-bold hover:opacity-70 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}
              >
                ×
              </button>
            </div>
            
            <div className="mb-4">
              <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Select which documents the AI should reference when answering your questions. 
                Selected documents will be used as context for better, more accurate responses.
              </p>
            </div>
            
            {loadingDocuments ? (
              <div className={`text-center py-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div className={`text-center py-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                <div className="text-4xl mb-4">📄</div>
                <p className="text-lg mb-2">No documents available</p>
                <p className="text-sm">Upload documents first to use them as context</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {documents.map((doc) => {
                  const isSelected = selectedDocuments.some(selected => selected.id === doc.id);
                  return (
                    <div 
                      key={doc.id} 
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        isSelected 
                          ? isDarkMode 
                            ? 'bg-blue-700 border-blue-500' 
                            : 'bg-blue-50 border-blue-300'
                          : isDarkMode 
                            ? 'bg-gray-700 border-gray-600 hover:bg-gray-600' 
                            : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedDocuments(prev => prev.filter(d => d.id !== doc.id));
                        } else {
                          setSelectedDocuments(prev => [...prev, doc]);
                        }
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}} // Handled by parent div onClick
                              className="w-4 h-4 text-blue-600 rounded"
                            />
                            <div>
                              <h4 className={`font-medium ${
                                isDarkMode ? 'text-white' : 'text-gray-900'
                              }`}>
                                {doc.filename}
                              </h4>
                              <div className={`text-sm mt-1 ${
                                isDarkMode ? 'text-gray-400' : 'text-gray-600'
                              }`}>
                                <div className="flex flex-wrap gap-4">
                                  <span>Size: {doc.size_bytes ? Math.round(doc.size_bytes / 1024) + ' KB' : 'Unknown'}</span>
                                  <span>Type: {doc.file_type || 'Unknown'}</span>
                                  <span>Words: {doc.word_count || 'Unknown'}</span>
                                </div>
                                <div className="mt-1">
                                  Uploaded: {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown'}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        {isSelected && (
                          <div className={`ml-4 px-2 py-1 rounded text-xs font-medium ${
                            isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800'
                          }`}>
                            Selected
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            <div className="flex justify-between items-center gap-4 mt-6">
              <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                {selectedDocuments.length} document{selectedDocuments.length !== 1 ? 's' : ''} selected
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedDocuments([])}
                  disabled={selectedDocuments.length === 0}
                  className={`px-4 py-2 rounded transition-colors ${
                    selectedDocuments.length === 0
                      ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                      : isDarkMode 
                        ? 'bg-gray-600 text-white hover:bg-gray-700' 
                        : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  }`}
                >
                  Clear All
                </button>
                <button
                  onClick={() => setShowDocumentSelector(false)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ClaudeLayout>
  );
};

export default ClaudeChatPage;