import { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';

const ChatMessageList = ({ messages, isLoading }) => {
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="flex-1 overflow-y-auto bg-white">
      {messages.length === 0 && !isLoading ? (
        <div className="h-full flex items-center justify-center">
          <div className="text-center px-4 py-10">
            <p className="text-gray-500 text-sm">
              No messages yet. Start a conversation by typing a message below.
            </p>
          </div>
        </div>
      ) : (
        messages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))
      )}
      
      {isLoading && (
        <div className="py-6 bg-gray-50 border-b border-gray-100">
          <div className="max-w-3xl mx-auto px-6">
            <div className="flex items-start">
              <div className="flex-1">
                <div className="flex items-center mb-2">
                  <div className="flex items-center">
                    <span className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center mr-2">
                      <span className="text-xs text-blue-600 font-medium">AI</span>
                    </span>
                    <h3 className="text-sm font-medium text-gray-800">Assistant</h3>
                  </div>
                </div>
                <div className="animate-pulse">
                  <div className="h-2 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-2 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-2 bg-gray-200 rounded w-2/3"></div>
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