import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

/**
 * Professional role-based route protection component
 * Provides secure access control with clean redirects and fallbacks
 */
const ProtectedRoute = ({ 
  children, 
  requireRole = null, 
  requirePermission = null,
  fallback = null,
  redirectTo = '/login',
  adminRedirect = '/unauthorized'
}) => {
  const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth()
  const location = useLocation()

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  // Check role-based access
  if (requireRole && !hasRole(requireRole)) {
    return fallback || <Navigate to={adminRedirect} replace />
  }

  // Check permission-based access
  if (requirePermission && !hasPermission(requirePermission)) {
    return fallback || <Navigate to={adminRedirect} replace />
  }

  return children
}

/**
 * Higher-order component for admin-only routes
 */
export const AdminRoute = ({ children, ...props }) => {
  return (
    <ProtectedRoute requireRole="admin" {...props}>
      {children}
    </ProtectedRoute>
  )
}

/**
 * Higher-order component for super admin-only routes
 */
export const SuperAdminRoute = ({ children, ...props }) => {
  return (
    <ProtectedRoute requireRole="superadmin" {...props}>
      {children}
    </ProtectedRoute>
  )
}

/**
 * Role-based conditional rendering component
 */
export const RoleGuard = ({ 
  children, 
  requireRole = null, 
  requirePermission = null,
  fallback = null,
  showForRoles = null 
}) => {
  const { hasRole, hasPermission, getUserRole } = useAuth()

  // Check specific roles array
  if (showForRoles && !showForRoles.includes(getUserRole())) {
    return fallback
  }

  // Check single role requirement
  if (requireRole && !hasRole(requireRole)) {
    return fallback
  }

  // Check permission requirement
  if (requirePermission && !hasPermission(requirePermission)) {
    return fallback
  }

  return children
}

export default ProtectedRoute