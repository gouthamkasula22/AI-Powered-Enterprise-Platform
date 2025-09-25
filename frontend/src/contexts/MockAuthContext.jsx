import React, { createContext, useContext, useState } from 'react';

// Mock Auth Context for testing UI
const MockAuthContext = createContext();

export const MockAuthProvider = ({ children }) => {
  const [user, setUser] = useState({
    id: 1,
    email: 'user@example.com',
    username: 'testuser',
    first_name: 'Test',
    last_name: 'User',
    display_name: 'Test User',
    role: 'user',
    is_verified: true
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  const login = async (credentials) => {
    setIsLoading(true);
    try {
      // Mock successful login
      console.log("Mock login with:", credentials);
      setIsAuthenticated(true);
      setUser({
        id: 1,
        email: credentials.email,
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        display_name: 'Test User',
        role: 'user',
        is_verified: true
      });
      return { success: true };
    } catch (error) {
      console.error("Mock login error", error);
      throw new Error("Invalid credentials");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      // Mock successful logout
      setIsAuthenticated(false);
      setUser(null);
      return { success: true };
    } catch (error) {
      console.error("Mock logout error", error);
      throw new Error("Logout failed");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUserData = async () => {
    // Mock refreshing user data
    console.log("Mock refreshing user data");
    return user;
  };

  const register = async (userData) => {
    setIsLoading(true);
    try {
      // Mock successful registration
      console.log("Mock register with:", userData);
      return { success: true };
    } catch (error) {
      console.error("Mock register error", error);
      throw new Error("Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MockAuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated,
      login,
      logout,
      register,
      refreshUserData
    }}>
      {children}
    </MockAuthContext.Provider>
  );
};

export const useMockAuth = () => {
  const context = useContext(MockAuthContext);
  if (context === undefined) {
    throw new Error('useMockAuth must be used within a MockAuthProvider');
  }
  return context;
};

export default MockAuthContext;