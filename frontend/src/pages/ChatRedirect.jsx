import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ClaudeLayout from '../components/layout/ClaudeLayout';

const ChatRedirect = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    // Redirect to the new chat page
    navigate('/chat/new', { replace: true });
  }, [navigate]);
  
  return (
    <ClaudeLayout>
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Redirecting to Chat Assistant...</p>
        </div>
      </div>
    </ClaudeLayout>
  );
};

export default ChatRedirect;