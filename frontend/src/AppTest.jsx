import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { MockAuthProvider } from './contexts/MockAuthContext';
import ClaudeChatPage from './pages/ClaudeChatPage';

function AppTest() {
  return (
    <Router>
      <ThemeProvider>
        <MockAuthProvider>
          <Routes>
            <Route path="/" element={<ClaudeChatPage />} />
          </Routes>
        </MockAuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default AppTest;