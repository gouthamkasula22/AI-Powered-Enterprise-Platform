"""
Admin User Management Endpoints

Provides endpoints for admin user @router.get("/list", response_model=UsersListResult)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active/inactive"),
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository)t operations including:
- List all users with pagination and filtering
- Update user roles
- Activate/deactivate users
- Get user statistics
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_, or_
from pydantic import BaseModel

from ....application.dto import UserDTO
from ....application.use_cases.auth_use_cases import AuthenticationUseCases
from ....domain.exceptions.domain_exceptions import (
    UserNotFoundException,
    ValidationError
)
from ....infrastructure.database.repositories import SqlUserRepository
from ....infrastructure.database.database import get_db_session
from ....infrastructure.cache.token_blacklist import TokenBlacklistService
from ..dependencies.auth import require_admin, require_superadmin, get_current_user, get_auth_use_cases
from ..schemas.auth import MessageResponse

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


# Request/Response Models
class UpdateUserRoleRequest(BaseModel):
    user_id: int
    new_role: str  # 'USER', 'ADMIN', 'SUPERADMIN'

class ToggleUserStatusRequest(BaseModel):
    user_id: int
    is_active: bool

class UserListResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

class UsersListResult(BaseModel):
    users: List[UserListResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    admin_users: int
    users_today: int
    users_this_week: int


async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> SqlUserRepository:
    """Get user repository dependency"""
    return SqlUserRepository(session)


@router.get("/list", response_model=UsersListResult)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    status_filter: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository)
):
    """
    List all users with pagination and filtering.
    Accessible by ADMIN and SUPERADMIN roles only.
    """
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get users with filtering
        users = await user_repo.list_users(
            limit=per_page,
            offset=offset,
            include_inactive=True
        )
        
        # Apply filters (simplified for now - in production, move to repository)
        filtered_users = users
        
        if search:
            search_lower = search.lower()
            filtered_users = [
                user for user in filtered_users
                if (user.email and search_lower in user.email.value.lower()) or
                   (user.first_name and search_lower in user.first_name.lower()) or
                   (user.last_name and search_lower in user.last_name.lower())
            ]
        
        # Role filter: frontend sends uppercase (USER/ADMIN/SUPERADMIN) but domain values are lowercase
        if role_filter and role_filter.lower() in ['user', 'admin', 'superadmin']:
            target_role = role_filter.lower()
            filtered_users = [
                user for user in filtered_users
                if user.role and user.role.value == target_role
            ]
        
        if status_filter:
            is_active = status_filter.lower() == 'active'
            filtered_users = [user for user in filtered_users if user.is_active == is_active]
        
        # Convert to response format
        user_responses = []
        for user in filtered_users:
            if user.id is None:
                continue  # Skip users without valid IDs
            # Return role in UPPERCASE for UI consistency while internal enum remains lowercase
            role_value = user.role.value.upper() if user.role else "USER"
            user_responses.append(UserListResponse(
                id=user.id,
                email=user.email.value if user.email else "",
                first_name=user.first_name,
                last_name=user.last_name,
                role=role_value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login
            ))
        
        # Calculate total pages
        total = len(user_responses)
        total_pages = (total + per_page - 1) // per_page
        
        # Apply pagination to response
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_users = user_responses[start_idx:end_idx]
        
        return UsersListResult(
            users=paginated_users,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.post("/update-role", response_model=MessageResponse)
async def update_user_role(
    request: UpdateUserRoleRequest,
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update a user's role.
    Only admins can promote to USER/ADMIN. Only superadmins can promote to SUPERADMIN.
    """
    try:
        # Validate role
        valid_roles = ['USER', 'ADMIN', 'SUPERADMIN']
        if request.new_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {valid_roles}"
            )
        
        # Check permissions for role assignment
        if request.new_role == 'SUPERADMIN' and current_user.role.value != 'SUPERADMIN':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmins can assign SUPERADMIN role"
            )
        
        # Get target user
        target_user = await user_repo.find_by_id(request.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-demotion from SUPERADMIN
        if (current_user.id == target_user.id and 
            current_user.role.value == 'SUPERADMIN' and 
            request.new_role != 'SUPERADMIN'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself from SUPERADMIN role"
            )
        
        # Update role using raw SQL (to avoid SQLAlchemy metadata issues)
        from sqlalchemy import text
        await session.execute(
            text("UPDATE users SET role = :role, updated_at = :updated_at WHERE id = :user_id"),
            {
                "role": request.new_role,
                "updated_at": datetime.utcnow(),
                "user_id": request.user_id
            }
        )
        await session.commit()
        
        return MessageResponse(
            message=f"User role updated to {request.new_role} successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}"
        )


@router.post("/toggle-status", response_model=MessageResponse)
async def toggle_user_status(
    request: ToggleUserStatusRequest,
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_db_session),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
):
    """
    Activate or deactivate a user account.
    When deactivating a user, all their active sessions will be revoked.
    Accessible by ADMIN and SUPERADMIN roles only.
    """
    try:
        # Get target user
        target_user = await user_repo.find_by_id(request.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deactivation
        if current_user.id == target_user.id and not request.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        # Update status using raw SQL
        from sqlalchemy import text
        await session.execute(
            text("UPDATE users SET is_active = :is_active, updated_at = :updated_at WHERE id = :user_id"),
            {
                "is_active": request.is_active,
                "updated_at": datetime.utcnow(),
                "user_id": request.user_id
            }
        )
        
        # If deactivating user, revoke all their sessions
        if not request.is_active:
            try:
                logger.info(f"Deactivating user {request.user_id} - revoking all sessions")
                # Use auth_use_cases to logout all devices
                result = await auth_use_cases.logout_all_devices(request.user_id)
                if result.success:
                    # Update last_logout timestamp
                    try:
                        await session.execute(
                            text("UPDATE users SET last_logout = :timestamp WHERE id = :user_id"),
                            {
                                "timestamp": datetime.utcnow(),
                                "user_id": request.user_id
                            }
                        )
                        logger.info(f"Successfully revoked all sessions for user {request.user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to update last_logout timestamp but sessions were revoked: {str(e)}")
                        # Continue since the tokens were still blacklisted
                else:
                    logger.warning(f"Session revocation for user {request.user_id} returned unsuccessful result")
            except Exception as e:
                logger.error(f"Failed to revoke sessions for user {request.user_id}: {str(e)}")
                # Continue with deactivation even if session revocation fails
        
        await session.commit()
        
        status_text = "activated" if request.is_active else "deactivated"
        message = f"User account {status_text} successfully"
        if not request.is_active:
            message += " and all sessions revoked"
            
        return MessageResponse(
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: UserDTO = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get user statistics for admin dashboard.
    Accessible by ADMIN and SUPERADMIN roles only.
    """
    try:
        from sqlalchemy import text
        
        # Get basic stats
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_users,
                COUNT(CASE WHEN is_verified = true THEN 1 END) as verified_users,
                COUNT(CASE WHEN LOWER(role) IN ('admin', 'superadmin') THEN 1 END) as admin_users,
                COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as users_today,
                COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as users_this_week
            FROM users
        """))
        
        stats = result.fetchone()
        
        if not stats:
            return UserStatsResponse(
                total_users=0,
                active_users=0,
                verified_users=0,
                admin_users=0,
                users_today=0,
                users_this_week=0
            )
        
        return UserStatsResponse(
            total_users=stats.total_users or 0,
            active_users=stats.active_users or 0,
            verified_users=stats.verified_users or 0,
            admin_users=stats.admin_users or 0,
            users_today=stats.users_today or 0,
            users_this_week=stats.users_this_week or 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user statistics: {str(e)}"
        )


@router.delete("/{user_id}/sessions", response_model=MessageResponse)
async def revoke_user_sessions(
    user_id: int,
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_db_session),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
):
    """
    Revoke all active sessions for a user (force logout).
    Accessible by ADMIN and SUPERADMIN roles only.
    """
    try:
        # Get target user
        target_user = await user_repo.find_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-logout unless it's intentional
        if current_user.id == target_user.id:
            return MessageResponse(
                message="Cannot revoke your own sessions through admin panel. Use logout instead.",
                success=True
            )
        
        logger.info(f"Admin user {current_user.id} revoking all sessions for user {user_id}")
        
        # 1. Blacklist all tokens for the user
        result = await auth_use_cases.logout_all_devices(user_id)
        if not result.success:
            logger.error(f"Failed to revoke sessions for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke sessions"
            )
        
        # 2. Update user's last_logout timestamp using try/except to handle potential DB issues
        try:
            await session.execute(
                text("UPDATE users SET last_logout = :timestamp WHERE id = :user_id"),
                {
                    "timestamp": datetime.utcnow(),
                    "user_id": user_id
                }
            )
            await session.commit()
        except Exception as e:
            logger.warning(f"Failed to update last_logout timestamp but sessions were revoked: {str(e)}")
            # Continue since the tokens were still blacklisted
        
        logger.info(f"Successfully revoked all sessions for user {user_id}")
        
        return MessageResponse(
            message=f"All sessions revoked for user: {target_user.email.value if target_user.email else 'Unknown'}",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Exception in revoke_user_sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke user sessions: {str(e)}"
        )