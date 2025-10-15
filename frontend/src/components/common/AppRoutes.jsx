import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from '../../pages/HomePage'
import LoginPage from '../../pages/LoginPage'
import RegisterPage from '../../pages/RegisterPage'
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
import ExcelPage from '../../pages/excel/ExcelPage'
import ExcelDocumentPage from '../../pages/excel/ExcelDocumentPage'

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
      
      {/* Chat routes - Default landing page after login */}
      <Route 
        path="/chat" 
        element={
          <ProtectedRoute>
            <Navigate to="/chat/new" replace />
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
      
      {/* Excel Q&A routes */}
      <Route 
        path="/excel" 
        element={
          <ProtectedRoute>
            <ExcelPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/excel/:id" 
        element={
          <ProtectedRoute>
            <ExcelDocumentPage />
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
