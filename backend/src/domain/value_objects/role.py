"""
User Role Value Object

Defines user roles and permissions for the RBAC system.
"""
from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    """
    User roles for Role-Based Access Control (RBAC)
    
    Roles are hierarchical:
    - USER: Basic user with standard permissions
    - ADMIN: Administrative user with elevated permissions
    - SUPERADMIN: Super administrator with full system access
    """
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    
    @property
    def permissions(self) -> Set[str]:
        """Get permissions associated with this role"""
        permission_map = {
            UserRole.USER: {
                "profile:read",
                "profile:update",
                "auth:login",
                "auth:logout",
                "auth:refresh"
            },
            UserRole.ADMIN: {
                "profile:read",
                "profile:update",
                "auth:login",
                "auth:logout", 
                "auth:refresh",
                "users:read",
                "users:list",
                "admin:dashboard"
            },
            UserRole.SUPERADMIN: {
                "profile:read",
                "profile:update",
                "auth:login",
                "auth:logout",
                "auth:refresh",
                "users:read",
                "users:list",
                "users:create",
                "users:update",
                "users:delete",
                "users:roles",
                "admin:dashboard",
                "admin:system"
            }
        }
        return permission_map.get(self, set())
    
    def has_permission(self, permission: str) -> bool:
        """Check if this role has a specific permission"""
        return permission in self.permissions
    
    def can_access_role(self, target_role: "UserRole") -> bool:
        """Check if this role can manage/access another role"""
        hierarchy = {
            UserRole.USER: 0,
            UserRole.ADMIN: 1,
            UserRole.SUPERADMIN: 2
        }
        
        current_level = hierarchy.get(self, -1)
        target_level = hierarchy.get(target_role, -1)
        
        return current_level >= target_level
    
    @classmethod
    def from_legacy_flags(cls, is_superuser: bool = False, is_staff: bool = False) -> "UserRole":
        """
        Convert legacy is_superuser/is_staff flags to new role system
        
        Args:
            is_superuser: Legacy superuser flag
            is_staff: Legacy staff flag
            
        Returns:
            Appropriate UserRole
        """
        if is_superuser:
            return cls.SUPERADMIN
        elif is_staff:
            return cls.ADMIN
        else:
            return cls.USER
    
    @classmethod
    def get_default_role(cls) -> "UserRole":
        """Get the default role for new users"""
        return cls.USER
    
    @classmethod
    def get_admin_roles(cls) -> List["UserRole"]:
        """Get list of administrative roles"""
        return [cls.ADMIN, cls.SUPERADMIN]
    
    @classmethod
    def get_all_roles(cls) -> List["UserRole"]:
        """Get list of all available roles"""
        return [cls.USER, cls.ADMIN, cls.SUPERADMIN]
    
    def __str__(self) -> str:
        """String representation of the role"""
        return self.value
    
    def __repr__(self) -> str:
        """Detailed representation of the role"""
        return f"UserRole.{self.name}"


class RoleValidationError(ValueError):
    """Raised when role validation fails"""
    pass


def validate_role(role: str) -> UserRole:
    """
    Validate and convert string to UserRole
    
    Args:
        role: Role string to validate
        
    Returns:
        UserRole enum
        
    Raises:
        RoleValidationError: If role is invalid
    """
    try:
        return UserRole(role.lower())
    except ValueError:
        valid_roles = [r.value for r in UserRole.get_all_roles()]
        raise RoleValidationError(
            f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"
        )


def get_role_hierarchy() -> dict:
    """
    Get role hierarchy for authorization checks
    
    Returns:
        Dictionary mapping roles to their hierarchy level
    """
    return {
        UserRole.USER: 0,
        UserRole.ADMIN: 1,
        UserRole.SUPERADMIN: 2
    }