# Role-Based Access Control (RBAC) System Documentation

## Overview

This document provides comprehensive documentation for the Role-Based Access Control (RBAC) system implementation in the User Authentication System. The RBAC system provides hierarchical role management with granular permissions and secure access control across both backend and frontend components.

## System Architecture

### Role Hierarchy

The system implements a three-tier role hierarchy:

1. **USER** (Level 1) - Basic user role
2. **ADMIN** (Level 2) - Administrative role with user management capabilities
3. **SUPERADMIN** (Level 3) - Highest privilege level with system-wide control

### Permission Inheritance

Roles inherit permissions from lower levels:
- **SUPERADMIN** has all ADMIN + USER permissions + system administration
- **ADMIN** has all USER permissions + user management
- **USER** has basic profile and authentication permissions

## Backend Implementation

### Domain Layer

#### UserRole Value Object (`backend/src/domain/value_objects/role.py`)

```python
class UserRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for this role"""
        
    def can_access_role(self, target_role: 'UserRole') -> bool:
        """Check if this role can access target role level"""
        
    def get_hierarchy_level(self) -> int:
        """Get numeric hierarchy level for comparison"""
```

**Key Features:**
- Enum-based role definition for type safety
- Permission mapping with inheritance
- Hierarchy level comparison
- Legacy user migration support

#### User Entity Updates

The User entity includes role field with business logic methods:

```python
@dataclass
class User:
    role: UserRole = UserRole.USER
    
    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        
    def can_manage_user(self, target_user: 'User') -> bool:
        """Check if user can manage another user"""
```

### Infrastructure Layer

#### Database Migration

Alembic migration adds role column with safe defaults:

```sql
-- Add role column with default value
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'USER' NOT NULL;

-- Migrate existing users
UPDATE users SET role = 'USER' WHERE role IS NULL;

-- Add index for performance
CREATE INDEX ix_users_role ON users(role);
```

#### Repository Updates

All repository methods updated to handle role field:

```python
def _domain_to_model(self, user: User) -> UserModel:
    return UserModel(
        role=user.role.value,
        # ... other fields
    )
    
def _model_to_domain(self, model: UserModel) -> User:
    return User(
        role=UserRole(model.role),
        # ... other fields
    )
```

### Presentation Layer

#### JWT Integration

JWT tokens include role information in payload:

```python
def create_access_token(self, user_data: dict) -> str:
    payload = {
        "sub": user_data["email"],
        "role": user_data["role"],
        "permissions": UserRole(user_data["role"]).get_permissions(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, self.secret_key, algorithm="HS256")
```

#### Role-Based Dependencies

FastAPI dependencies for endpoint protection:

```python
async def require_admin(current_user: User = Depends(get_current_user)):
    """Require ADMIN role or higher"""
    if not current_user.has_role(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_superadmin(current_user: User = Depends(get_current_user)):
    """Require SUPERADMIN role"""
    if not current_user.has_role(UserRole.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user
```

#### Protected Endpoints

Role-based endpoint protection:

```python
@router.get("/admin/dashboard")
async def admin_dashboard(admin_user: User = Depends(require_admin)):
    """Admin dashboard - ADMIN+ only"""
    return {"message": f"Welcome to admin dashboard, {admin_user.email}"}

@router.get("/admin/system")
async def system_settings(superadmin_user: User = Depends(require_superadmin)):
    """System settings - SUPERADMIN only"""
    return {"message": "System settings access granted"}
```

## Frontend Implementation

### Authentication Context

Enhanced with role-based helpers:

```javascript
const AuthProvider = ({ children }) => {
  // Role-based access helpers
  const getUserRole = useCallback(() => user?.role || 'USER', [user])
  
  const hasRole = useCallback((requiredRole) => {
    const roleHierarchy = { 'USER': 1, 'ADMIN': 2, 'SUPERADMIN': 3 }
    return (roleHierarchy[getUserRole()] || 0) >= (roleHierarchy[requiredRole] || 0)
  }, [getUserRole])
  
  const hasPermission = useCallback((permission) => {
    const rolePermissions = {
      'USER': ['read_own_profile'],
      'ADMIN': ['read_own_profile', 'read_users', 'manage_users'],
      'SUPERADMIN': ['read_own_profile', 'read_users', 'manage_users', 'manage_admins', 'system_admin']
    }
    return rolePermissions[getUserRole()]?.includes(permission) || false
  }, [getUserRole])
}
```

### Route Protection

Professional route protection components:

```javascript
// Basic protected route
const ProtectedRoute = ({ children, requireRole, requirePermission, fallback, redirectTo }) => {
  // Route protection logic
}

// Admin-only routes
const AdminRoute = ({ children, ...props }) => (
  <ProtectedRoute requireRole="ADMIN" {...props}>
    {children}
  </ProtectedRoute>
)

// Super admin-only routes
const SuperAdminRoute = ({ children, ...props }) => (
  <ProtectedRoute requireRole="SUPERADMIN" {...props}>
    {children}
  </ProtectedRoute>
)
```

### Conditional Rendering

Role-based component visibility:

```javascript
const RoleGuard = ({ children, requireRole, requirePermission, fallback, showForRoles }) => {
  const { hasRole, hasPermission, getUserRole } = useAuth()
  
  // Check access conditions
  if (showForRoles && !showForRoles.includes(getUserRole())) return fallback
  if (requireRole && !hasRole(requireRole)) return fallback
  if (requirePermission && !hasPermission(requirePermission)) return fallback
  
  return children
}
```

### Admin Interface

Professional admin dashboard with clean design:

- **Admin Dashboard** (`/admin`) - Overview and quick actions
- **User Management** (`/admin/users`) - User account management
- **System Settings** (`/admin/system`) - Super admin system configuration

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Role Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/v1/auth/register` | None | User registration |
| POST | `/api/v1/auth/login` | None | User login with role info |
| GET | `/api/v1/auth/me` | USER+ | Current user profile |

### Admin Endpoints

| Method | Endpoint | Role Required | Description |
|--------|----------|---------------|-------------|
| GET | `/api/v1/admin/dashboard` | ADMIN+ | Admin dashboard data |
| GET | `/api/v1/admin/users` | ADMIN+ | List all users |
| PUT | `/api/v1/admin/users/{id}/role` | SUPERADMIN | Update user role |
| GET | `/api/v1/admin/system` | SUPERADMIN | System settings |

### Testing Endpoints

| Method | Endpoint | Role Required | Description |
|--------|----------|---------------|-------------|
| GET | `/api/v1/admin/test/role-check` | USER+ | Role validation test |
| GET | `/api/v1/admin/test/rbac-demo` | USER+ | RBAC demonstration |
| GET | `/api/v1/admin/superadmin` | SUPERADMIN | Super admin test |

## Testing

### RBAC Testing Script

Comprehensive testing script validates:

- User registration with default USER role
- JWT token role inclusion
- Role-based endpoint access control
- Permission hierarchy enforcement
- Admin functionality

Run the test:

```bash
python scripts/comprehensive_rbac_test.py
```

### Test Coverage

The testing script validates:

1. **Basic Connectivity** - API health check
2. **User Registration** - All role types
3. **Authentication** - Login with role information
4. **JWT Validation** - Token payload role inclusion
5. **Access Control** - Role-based endpoint protection
6. **RBAC Demo** - Complete system demonstration

## Error Handling

### Professional Error Management

Comprehensive error handling system:

```javascript
const useRoleErrorHandler = () => {
  const handleError = (error, context = {}) => {
    const parsedError = parseError(error)
    // Role-specific error messages
    displayError(enrichedError)
    return enrichedError
  }
}
```

### Error Types

- **Authentication Errors** - Login/token issues
- **Authorization Errors** - Insufficient permissions
- **Validation Errors** - Input validation failures
- **System Errors** - Server/network issues

## Security Considerations

### Backend Security

1. **JWT Security** - Secure token generation and validation
2. **Role Validation** - Server-side role checking on every request
3. **Database Security** - Role column with proper constraints
4. **Permission Checks** - Granular permission validation

### Frontend Security

1. **Client-side Protection** - UI hiding for unauthorized features
2. **Route Protection** - Secure routing with role validation
3. **Token Management** - Secure token storage and refresh
4. **Error Handling** - Secure error messages without information leakage

## Deployment Considerations

### Database Migration

1. Run Alembic migration to add role column
2. Migrate existing users to USER role
3. Update any existing admin users manually

### Environment Variables

Required environment variables:
- `JWT_SECRET_KEY` - JWT signing key
- `DEFAULT_USER_ROLE` - Default role for new users (USER)

### Performance

1. **Database Indexing** - Index on role column for fast queries
2. **JWT Caching** - Consider JWT caching for high-traffic scenarios
3. **Permission Caching** - Cache permission calculations

## Future Enhancements

### Potential Improvements

1. **Dynamic Permissions** - Database-driven permission system
2. **Role Groups** - Multiple role assignment per user
3. **Time-based Roles** - Temporary role elevation
4. **Audit Logging** - Role change audit trail
5. **API Rate Limiting** - Role-based rate limiting

### Scalability

1. **Microservices** - Split RBAC into dedicated service
2. **Caching Layer** - Redis for permission caching
3. **External Identity** - Integration with external identity providers

## Troubleshooting

### Common Issues

1. **Migration Failures** - Check database constraints
2. **JWT Token Issues** - Verify secret key configuration
3. **Permission Errors** - Check role hierarchy implementation
4. **Frontend Access** - Verify route protection setup

### Debug Tools

1. **RBAC Test Script** - Comprehensive system validation
2. **JWT Decoder** - Inspect token payloads
3. **Database Queries** - Verify role data integrity
4. **Browser Dev Tools** - Check frontend role state

## Conclusion

The RBAC system provides comprehensive role-based access control with:

- **Secure Backend** - Complete domain-driven role management
- **Professional Frontend** - Clean, role-aware user interface
- **Comprehensive Testing** - Automated validation of all components
- **Production Ready** - Secure, scalable, and maintainable implementation

The system successfully implements the requested features:
- ✅ Role column added to users table
- ✅ JWT payload includes user role
- ✅ Protected admin endpoints
- ✅ Professional frontend with minimal design
- ✅ Complete role hierarchy and permissions
- ✅ Comprehensive testing and documentation

For questions or issues, refer to the troubleshooting section or run the comprehensive test script for system validation.