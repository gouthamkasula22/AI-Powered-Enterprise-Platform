"""
Admin Endpoints

Protected admin-only endpoints for testing the RBAC system.
These endpoints demonstrate role-based access control in action.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ....application.dto import UserDTO
from ....domain.value_objects.role import UserRole
from ..dependencies.auth import (
    require_admin,
    require_superadmin,
    require_role,
    require_permission,
    get_current_user
)
from ..schemas.auth import MessageResponse


router = APIRouter(tags=["admin"])


@router.get("/dashboard", response_model=dict)
async def admin_dashboard(
    current_user: UserDTO = Depends(require_admin)
):
    """
    Admin dashboard endpoint.
    Accessible by ADMIN and SUPERADMIN roles only.
    This demonstrates role-based access control.
    """
    return {
        "message": f"Welcome to admin dashboard, {current_user.first_name or current_user.email}!",
        "user_role": current_user.role.value,
        "user_permissions": current_user.role.permissions,
        "dashboard_data": {
            "admin_access_granted": True,
            "user_id": current_user.id,
            "session_info": "Active admin session"
        },
        "rbac_info": {
            "required_role": "ADMIN or higher",
            "user_has_access": True,
            "role_hierarchy": "USER < ADMIN < SUPERADMIN"
        }
    }


@router.get("/superadmin", response_model=dict)
async def superadmin_panel(
    current_user: UserDTO = Depends(require_superadmin)
):
    """
    Superadmin panel endpoint.
    Accessible by SUPERADMIN role only.
    This demonstrates the highest level of role-based access control.
    """
    return {
        "message": f"Welcome to superadmin panel, {current_user.first_name or current_user.email}!",
        "user_role": current_user.role.value,
        "user_permissions": current_user.role.permissions,
        "superadmin_data": {
            "superadmin_access_granted": True,
            "user_id": current_user.id,
            "highest_privilege": True
        },
        "rbac_info": {
            "required_role": "SUPERADMIN only",
            "user_has_access": True,
            "access_level": "Maximum privileges"
        }
    }


@router.get("/test/role-check")
async def test_role_check(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Test endpoint to check current user's role and permissions.
    Available to any authenticated user for testing purposes.
    """
    return {
        "user_info": {
            "email": current_user.email,
            "role": current_user.role.value,
            "permissions": current_user.role.permissions
        },
        "access_matrix": {
            "can_access_user_endpoints": current_user.role in [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN],
            "can_access_admin_endpoints": current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN],
            "can_access_superadmin_endpoints": current_user.role == UserRole.SUPERADMIN
        },
        "role_hierarchy": {
            "USER": {
                "level": 1,
                "permissions": UserRole.USER.permissions
            },
            "ADMIN": {
                "level": 2,
                "permissions": UserRole.ADMIN.permissions
            },
            "SUPERADMIN": {
                "level": 3,
                "permissions": UserRole.SUPERADMIN.permissions
            }
        }
    }


@router.post("/test/permission-check")
async def test_permission_check(
    permission: str,
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Test endpoint to check if current user has a specific permission.
    Useful for testing the permission-based access control.
    """
    user_permissions = current_user.role.permissions
    has_permission = permission in user_permissions
    
    return {
        "test_results": {
            "requested_permission": permission,
            "user_has_permission": has_permission,
            "user_role": current_user.role.value,
            "user_permissions": user_permissions
        },
        "available_permissions": {
            "user_role_permissions": UserRole.USER.permissions,
            "admin_role_permissions": UserRole.ADMIN.permissions,
            "superadmin_role_permissions": UserRole.SUPERADMIN.permissions
        }
    }


@router.get("/test/rbac-demo")
async def rbac_demonstration(
    current_user: UserDTO = Depends(get_current_user)
):
    """
    Comprehensive RBAC demonstration endpoint.
    Shows complete role-based access control implementation.
    """
    return {
        "rbac_demo": {
            "current_user": {
                "email": current_user.email,
                "role": current_user.role.value,
                "permissions": current_user.role.permissions,
                "user_id": current_user.id
            },
            "system_info": {
                "rbac_enabled": True,
                "available_roles": [role.value for role in UserRole],
                "role_hierarchy": "USER < ADMIN < SUPERADMIN",
                "permission_inheritance": "Higher roles inherit all lower role permissions"
            },
            "endpoint_access": {
                "/admin/dashboard": "ADMIN+ required" if current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN] else "Access Denied",
                "/admin/superadmin": "SUPERADMIN required" if current_user.role == UserRole.SUPERADMIN else "Access Denied",
                "/admin/test/*": "Any authenticated user"
            },
            "jwt_payload": {
                "contains_role": True,
                "contains_permissions": True,
                "role_verified": current_user.role.value,
                "permissions_verified": len(current_user.role.permissions)
            }
        }
    }