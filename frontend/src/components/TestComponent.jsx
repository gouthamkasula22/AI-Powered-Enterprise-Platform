// This is a test file to verify imports
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const TestComponent = () => {
  const { user } = useAuth();
  const { isDarkMode } = useTheme();
  
  return (
    <div>
      <h1>Test Component</h1>
      <p>User: {user?.name || 'Not logged in'}</p>
      <p>Theme: {isDarkMode ? 'Dark' : 'Light'}</p>
    </div>
  );
};

export default TestComponent;