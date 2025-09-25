import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import ClaudeLayout from '../components/layout/ClaudeLayout';

const HelpPage = () => {
  const { isDarkMode } = useTheme();
  const { user } = useAuth();

  return (
    <ClaudeLayout>
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Help & FAQ</h1>
        
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
            <p className="mb-4">
              Welcome to our Chat Assistant! This guide will help you make the most of your chat experience.
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Start a new chat by clicking the "New Chat" button in the sidebar</li>
              <li>View your chat history in the sidebar</li>
              <li>Access your account settings by clicking on your profile picture</li>
            </ul>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Frequently Asked Questions</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-orange-500">How do I start a new conversation?</h3>
                <p className="mt-1">Click on the "New Chat" button in the sidebar to start a fresh conversation.</p>
              </div>
              
              <div>
                <h3 className="font-medium text-orange-500">Can I delete my chat history?</h3>
                <p className="mt-1">Yes, you can delete individual conversations by clicking on the three dots next to each conversation in your chat history.</p>
              </div>
              
              <div>
                <h3 className="font-medium text-orange-500">How do I change my password?</h3>
                <p className="mt-1">Go to your profile by clicking on your avatar, then navigate to the Security page to change your password.</p>
              </div>
              
              <div>
                <h3 className="font-medium text-orange-500">Is my conversation data secure?</h3>
                <p className="mt-1">Yes, all conversations are encrypted and stored securely. We respect your privacy and do not share your data with third parties.</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Contact Support</h2>
            <p className="mb-4">
              If you need further assistance, please don't hesitate to contact our support team:
            </p>
            <p className="flex items-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span>support@example.com</span>
            </p>
          </div>
        </div>
      </div>
    </ClaudeLayout>
  );
};

export default HelpPage;