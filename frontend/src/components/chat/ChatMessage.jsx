import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const isAI = message.role === 'assistant';
  const isUser = message.role === 'user';
  
  return (
    <div className={`py-6 ${isAI ? 'bg-gray-50' : 'bg-white'} border-b border-gray-100`}>
      <div className="max-w-3xl mx-auto px-6">
        <div className="flex items-start">
          {/* Message content */}
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <div className="flex items-center">
                {isAI ? (
                  <span className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center mr-2">
                    <span className="text-xs text-blue-600 font-medium">AI</span>
                  </span>
                ) : null}
                <h3 className="text-sm font-medium text-gray-800">
                  {isAI ? 'Assistant' : 'You'}
                </h3>
              </div>
              <span className="ml-2 text-xs text-gray-400">
                {new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </span>
              
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="ml-auto text-xs text-gray-400 hover:text-gray-600"
                aria-label={isExpanded ? "Collapse message" : "Expand message"}
              >
                {isExpanded ? 'Collapse' : 'Expand'}
              </button>
            </div>
            
            {isExpanded && (
              <div className="prose prose-sm max-w-none">
                {isAI ? (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                ) : (
                  <p>{message.content}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;