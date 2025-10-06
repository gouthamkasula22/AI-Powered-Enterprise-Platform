import { useState } from 'react';

const ChatInput = ({ onSendMessage, onImageCommand, disabled, placeholder = "Message Assistant..." }) => {
  const [message, setMessage] = useState('');
  const [chatMode, setChatMode] = useState('general');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      const trimmedMessage = message.trim().toLowerCase();
      
      // Check for explicit /image command first
      if (message.trim().startsWith('/image ')) {
        const imagePrompt = message.trim().substring(7); // Remove '/image '
        if (imagePrompt && onImageCommand) {
          // First send the user message through normal flow
          onSendMessage(message, chatMode);
          // Then trigger image generation
          onImageCommand(imagePrompt);
          setMessage('');
          return;
        }
      }
      
      // Auto-detect image generation requests
      const imageKeywords = [
        'generate an image of', 'generate an image', 'create an image of', 'create an image', 
        'make an image of', 'make an image', 'draw an image of', 'draw an image',
        'generate a picture of', 'generate a picture', 'create a picture of', 'create a picture', 
        'make a picture of', 'make a picture', 'draw a picture of', 'draw a picture',
        'generate a photo of', 'generate a photo', 'create a photo of', 'create a photo', 
        'make a photo of', 'make a photo',
        'generate image of', 'generate image', 'create image of', 'create image', 
        'make image of', 'make image', 'draw image of', 'draw image',
        'show me an image of', 'show me an image', 'show me a picture of', 'show me a picture', 
        'show me a photo of', 'show me a photo',
        'can you draw', 'can you create', 'can you generate', 'can you make',
        'i want an image of', 'i want an image', 'i want a picture of', 'i want a picture', 
        'i want a photo of', 'i want a photo',
        'paint', 'sketch', 'illustrate', 'visualize'
      ];
      
      const isImageRequest = imageKeywords.some(keyword => trimmedMessage.includes(keyword));
      
      console.log('Debug - Message:', message);
      console.log('Debug - Trimmed message:', trimmedMessage);
      console.log('Debug - Is image request:', isImageRequest);
      console.log('Debug - Has onImageCommand:', !!onImageCommand);
      console.log('Debug - Matching keywords:', imageKeywords.filter(keyword => trimmedMessage.includes(keyword)));
      
      if (isImageRequest && onImageCommand) {
        console.log('Debug - Image request detected! Triggering image generation...');
        // Extract the prompt by removing common prefixes
        let imagePrompt = message.trim();
        const prefixesToRemove = [
          'generate an image of', 'create an image of', 'make an image of', 'draw an image of',
          'generate a picture of', 'create a picture of', 'make a picture of', 'draw a picture of',
          'generate a photo of', 'create a photo of', 'make a photo of',
          'generate image of', 'create image of', 'make image of', 'draw image of',
          'show me an image of', 'show me a picture of', 'show me a photo of',
          'can you draw', 'can you create', 'can you generate', 'can you make',
          'i want an image of', 'i want a picture of', 'i want a photo of',
          'paint', 'sketch', 'illustrate', 'visualize'
        ];
        
        // Remove the most specific matching prefix
        for (const prefix of prefixesToRemove.sort((a, b) => b.length - a.length)) {
          if (trimmedMessage.startsWith(prefix)) {
            imagePrompt = message.trim().substring(prefix.length).trim();
            break;
          }
        }
        
        // If no specific prefix found, use the whole message
        if (imagePrompt === message.trim()) {
          // Try to extract after common words
          const extractionPatterns = [
            /(?:generate|create|make|draw|paint|sketch|illustrate|visualize)\s+(?:an?\s+)?(?:image|picture|photo)?\s*(?:of\s+)?(.+)/i,
            /(?:show me|i want)\s+(?:an?\s+)?(?:image|picture|photo)\s*(?:of\s+)?(.+)/i,
            /(?:can you)\s+(?:draw|create|generate|make)\s+(.+)/i
          ];
          
          for (const pattern of extractionPatterns) {
            const match = message.trim().match(pattern);
            if (match && match[1]) {
              imagePrompt = match[1].trim();
              break;
            }
          }
        }
        
        if (imagePrompt && imagePrompt !== message.trim()) {
          // First send the user message through normal flow
          onSendMessage(message, chatMode);
          // Then trigger image generation
          onImageCommand(imagePrompt);
          setMessage('');
          return;
        }
      }
      
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
          <br />
          <span className="text-blue-600">🎨 Image generation: Type "/image [description]" or naturally like "generate an image of..."</span>
        </p>
      </form>
    </div>
  );
};

export default ChatInput;