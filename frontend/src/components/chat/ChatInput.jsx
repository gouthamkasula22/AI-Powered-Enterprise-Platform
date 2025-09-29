import { useState } from 'react';

const ChatInput = ({ onSendMessage, disabled, placeholder = "Message Assistant..." }) => {
  const [message, setMessage] = useState('');
  const [chatMode, setChatMode] = useState('general');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message, chatMode);
      setMessage('');
    }
  };
  
  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        {/* Chat Mode Selector */}
        <div className="flex items-center mb-3">
          <label className="text-sm font-medium text-gray-700 mr-3">Chat Mode:</label>
          <div className="flex bg-gray-100 rounded-md p-1">
            <button
              type="button"
              onClick={() => setChatMode('general')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                chatMode === 'general'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              General Chat
            </button>
            <button
              type="button"
              onClick={() => setChatMode('rag')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                chatMode === 'rag'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Document-Based
            </button>
          </div>
        </div>
        <div className="flex">
          <div className="flex-1">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={placeholder}
              rows={1}
              className="block w-full px-4 py-2.5 border border-gray-200 rounded-md shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              disabled={disabled}
              style={{ resize: 'none' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
          </div>
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className={`
              ml-2 px-4 py-2 rounded-md shadow-sm text-sm font-medium text-white
              ${disabled || !message.trim() 
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'}
            `}
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1.5 ml-1">
          Press Enter to send, Shift+Enter for new line
          {chatMode === 'general' ? ' • General AI mode' : ' • Document-based mode'}
        </p>
      </form>
    </div>
  );
};

export default ChatInput;