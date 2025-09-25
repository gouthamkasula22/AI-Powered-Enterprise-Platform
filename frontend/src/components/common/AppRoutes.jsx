import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from '../../pages/HomePage'
import LoginPage from '../../pages/LoginPage'
import RegisterPage from '../../pages/RegisterPage'
import DashboardPage from '../../pages/DashboardPage'
import ChatRedirect from '../../pages/ChatRedirect'
import ClaudeChatPage from '../../pages/ClaudeChatPage'
import VerifyEmailPage from '../../pages/VerifyEmailPage'
import ForgotPasswordPage from '../../pages/ForgotPasswordPage'
import ResetPasswordPage from '../../pages/ResetPasswordPage'
import OAuthCallback from '../../pages/auth/OAuthCallback'
import UnauthorizedPage from '../../pages/UnauthorizedPage'
import ProfilePage from '../../pages/ProfilePage'
import SecurityPage from '../../pages/SecurityPage'
import SettingsPage from '../../pages/SettingsPage'
import OverviewPage from '../../pages/OverviewPage'
import HelpPage from '../../pages/HelpPage'
import ProtectedRoute, { AdminRoute, SuperAdminRoute } from '../ProtectedRoute'
import AdminDashboard from '../../pages/admin/AdminDashboard'
import UserManagement from '../../pages/admin/UserManagement'
import SystemSettings from '../../pages/admin/SystemSettings'

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      
      {/* Protected user routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } 
      />
      
      {/* Chat routes */}
      <Route 
        path="/chat" 
        element={
          <ProtectedRoute>
            <ChatRedirect />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/chat/:threadId" 
        element={
          <ProtectedRoute>
            <ClaudeChatPage />
          </ProtectedRoute>
        } 
      />
      
      {/* User profile routes */}
      <Route
        path="/user/overview"
        element={
          <ProtectedRoute>
            <OverviewPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/user/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/user/security"
        element={
          <ProtectedRoute>
            <SecurityPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/user/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="/user/help"
        element={
          <ProtectedRoute>
            <HelpPage />
          </ProtectedRoute>
        }
      />
      
      {/* Admin-only routes */}
      <Route 
        path="/admin" 
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        } 
      />
      <Route 
        path="/admin/users" 
        element={
          <AdminRoute>
            <UserManagement />
          </AdminRoute>
        } 
      />
      
      {/* Super admin-only routes */}
      <Route 
        path="/admin/system" 
        element={
          <SuperAdminRoute>
            <SystemSettings />
          </SuperAdminRoute>
        } 
      />
      
      {/* Redirect any unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
