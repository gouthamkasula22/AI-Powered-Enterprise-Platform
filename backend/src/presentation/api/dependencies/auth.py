"""
Authentication Dependencies

FastAPI dependency injection for authentication and authorization.
Provides current user, authentication services, and use cases.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from ....application.dto import UserDTO
from ....application.use_cases.auth_use_cases import AuthenticationUseCases
from ....application.use_cases.user_use_cases import UserManagementUseCases
from ....infrastructure.database.database import get_db_session
from ....infrastructure.database.repositories import SqlUserRepository
from ....infrastructure.security.jwt_service import JWTService, AuthenticationService, TokenBlacklistService
from ....infrastructure.email.email_service import SMTPEmailService
from ....infrastructure.email.template_service import SimpleTemplateService
from ....infrastructure.cache import get_cache_service_dep
from ....shared.config import get_settings
from ....domain.exceptions.domain_exceptions import ValidationError, UserNotFoundException, AccountDeactivatedException
from ....domain.exceptions.auth_exceptions import TokenBlacklistedException
from ....domain.value_objects.role import UserRole
import logging
from ....shared.config import get_settings
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


def get_user_repository(
    db: AsyncSession = Depends(get_db_session)
) -> SqlUserRepository:
    """Get user repository with database session"""
    return SqlUserRepository(db)


def get_jwt_service() -> JWTService:
    """Get JWT service instance with configuration"""
    settings = get_settings()
    return JWTService(
        secret_key=settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
        access_token_expire_minutes=settings.auth_access_token_expire_minutes,
        refresh_token_expire_days=settings.auth_refresh_token_expire_days
    )


async def get_blacklist_service(
    cache_service = Depends(get_cache_service_dep)
) -> TokenBlacklistService:
    """Get token blacklist service instance"""
    return TokenBlacklistService(cache_service)


def get_auth_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    blacklist_service: TokenBlacklistService = Depends(get_blacklist_service)
) -> AuthenticationService:
    """Get authentication service with JWT and blacklist services"""
    return AuthenticationService(jwt_service, blacklist_service)


def get_email_service() -> SMTPEmailService:
    """Get email service instance"""
    settings = get_settings()
    return SMTPEmailService(
        smtp_server=settings.smtp_host,
        smtp_port=settings.smtp_port,
        username=settings.smtp_username or "",
        password=settings.smtp_password or "",
        use_tls=settings.smtp_use_tls,
        default_from_email=settings.smtp_from_email,
        default_from_name=settings.smtp_from_name
    )


def get_template_service() -> SimpleTemplateService:
    """Get template service instance"""
    return SimpleTemplateService()


async def get_auth_use_cases(
    user_repo: SqlUserRepository = Depends(get_user_repository),
    auth_service: AuthenticationService = Depends(get_auth_service),
    email_service: SMTPEmailService = Depends(get_email_service),
    template_service: SimpleTemplateService = Depends(get_template_service)
) -> AuthenticationUseCases:
    """Get authentication use cases with all dependencies"""
    return AuthenticationUseCases(user_repo, auth_service, email_service, template_service)


async def get_user_use_cases(
    user_repo: SqlUserRepository = Depends(get_user_repository)
) -> UserManagementUseCases:
    """Get user management use cases with all dependencies"""
    return UserManagementUseCases(user_repo)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> Optional[UserDTO]:
    """
    Get current user from JWT token (optional)
    Returns None if no token or invalid token
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        # Validate token and get user
        user = await auth_use_cases.get_current_user(token)
        return user
    except (ValidationError, UserNotFoundException):
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases),
    user_repo = Depends(get_user_repository)
) -> UserDTO:
    """
    Get current user from JWT token (required)
    Raises HTTPException if no token or invalid token
    """
    try:
        token = credentials.credentials
        # Validate token and get user
        user = await auth_use_cases.get_current_user(token)
        
        # Check if user is deactivated
        db_user = await user_repo.find_by_id(user.id)
        if db_user and not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "USER_DEACTIVATED",
                    "message": "Your account has been deactivated. Please contact an administrator."
                },
            )
            
        return user
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    except TokenBlacklistedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "TOKEN_BLACKLISTED", "message": "Token has been blacklisted or revoked"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "USER_NOT_FOUND", "message": "User not found"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    except AccountDeactivatedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACCOUNT_DISABLED", "message": "Account is disabled"},
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    current_user: UserDTO = Depends(get_current_user)
) -> UserDTO:
    """
    Get current active user (must be verified and not disabled)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "EMAIL_NOT_VERIFIED", "message": "Email address not verified"}
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACCOUNT_DISABLED", "message": "Account is disabled"}
        )
    
    return current_user


async def get_admin_user(
    current_user: UserDTO = Depends(get_current_active_user)
) -> UserDTO:
    """
    Get current user with admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "INSUFFICIENT_PRIVILEGES", "message": "Admin privileges required"}
        )
    
    return current_user


def require_permissions(*required_permissions: str):
    """
    Dependency factory for role-based access control
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: UserDTO = Depends(require_permissions("admin"))
        ):
            pass
    """
    async def permission_checker(
        current_user: UserDTO = Depends(get_current_active_user)
    ) -> UserDTO:
        user_permissions = set(current_user.permissions or [])
        required_perms = set(required_permissions)
        
        if not required_perms.issubset(user_permissions):
            missing_perms = required_perms - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Missing permissions: {', '.join(missing_perms)}"
                }
            )
        
        return current_user
    
    return permission_checker


# New Role-Based Dependencies

def _extract_role_value(role_obj) -> str:
    """
    Safely extract lowercase role value from possible Enum or string representations.
    Handles both database values (uppercase) and enum values (lowercase).
    """
    if role_obj is None:
        return ""
    
    try:
        # Handle UserRole enum instance
        if isinstance(role_obj, UserRole):
            return role_obj.value.lower()
        
        # Handle string representation
        text = str(role_obj).strip()
        if not text:
            return ""
        
        # Handle qualified Enum repr like 'UserRole.ADMIN'
        if '.' in text:
            text = text.split('.')[-1]
        
        # Convert to lowercase for consistent comparison
        # This handles both database values ("ADMIN") and enum values ("admin")
        normalized = text.lower()
        
        # Map common variations to standard values
        role_mapping = {
            'admin': 'admin',
            'administrator': 'admin',
            'superadmin': 'superadmin',
            'super_admin': 'superadmin',
            'superadministrator': 'superadmin',
            'user': 'user',
            'member': 'user'
        }
        
        return role_mapping.get(normalized, normalized)
        
    except Exception as e:
        # Log the error for debugging but don't crash
        logger.warning("Failed to extract role value from %s: %s", role_obj, e)
        return ""

def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: UserDTO = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN))
        ):
            pass
    """
    async def role_checker(
        current_user: UserDTO = Depends(get_current_active_user)
    ) -> UserDTO:
        # Check if user has any of the allowed roles
        current_role_value = _extract_role_value(current_user.role)
        allowed_values = [role.value for role in allowed_roles]
        if current_role_value not in allowed_values:
            allowed_role_names = [role.value for role in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_ROLE",
                    "message": f"Required role: {', '.join(allowed_role_names)}. Current role: {current_role_value or current_user.role}"
                }
            )
        
        return current_user
    
    return role_checker


def require_permission(*required_permissions: str):
    """
    Dependency factory for permission-based access control
    
    Usage:
        @router.get("/users")
        async def list_users(
            user: UserDTO = Depends(require_permission("users:read"))
        ):
            pass
    """
    async def permission_checker(
        current_user: UserDTO = Depends(get_current_active_user)
    ) -> UserDTO:
        # Get user's permissions from their role
        role_value = _extract_role_value(current_user.role) or 'user'
        try:
            user_role = UserRole(role_value)
        except ValueError:
            user_role = UserRole.USER
        user_permissions = user_role.permissions
        
        required_perms = set(required_permissions)
        
        if not required_perms.issubset(user_permissions):
            missing_perms = required_perms - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Missing permissions: {', '.join(missing_perms)}"
                }
            )
        
        return current_user
    
    return permission_checker


async def require_admin(
    current_user: UserDTO = Depends(get_current_active_user)
) -> UserDTO:
    """
    Require admin role (ADMIN or SUPERADMIN)
    Handles both uppercase (database) and lowercase (enum) role values
    """
    # Extract and normalize the role value (converts to lowercase)
    user_role = _extract_role_value(current_user.role)
    admin_roles = [UserRole.ADMIN.value, UserRole.SUPERADMIN.value]  # 'admin', 'superadmin'
    
    # Enhanced debugging
    settings = get_settings()
    if getattr(settings, 'debug', False):
        logger.debug(
            "require_admin check: user_id=%s, original_role='%s', normalized_role='%s', expected_roles=%s", 
            getattr(current_user, 'id', 'unknown'), 
            current_user.role, 
            user_role, 
            admin_roles
        )
    
    # Check if user has admin privileges
    if user_role not in admin_roles:
        # Additional fallback check for is_superuser or is_admin flags
        is_superuser = getattr(current_user, 'is_superuser', False)
        is_admin = getattr(current_user, 'is_admin', False)
        
        if is_superuser or is_admin:
            if getattr(settings, 'debug', False):
                logger.debug("require_admin ALLOW via flag: is_superuser=%s, is_admin=%s", is_superuser, is_admin)
            return current_user
        
        if getattr(settings, 'debug', False):
            logger.debug(
                "require_admin DENY: role='%s', expected=%s, is_superuser=%s, is_admin=%s", 
                user_role, admin_roles, is_superuser, is_admin
            )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ADMIN_REQUIRED", 
                "message": f"Admin privileges required. Current role: {current_user.role}"
            }
        )
    
    if getattr(settings, 'debug', False):
        logger.debug("require_admin ALLOW: role='%s'", user_role)
    return current_user


async def require_superadmin(
    current_user: UserDTO = Depends(get_current_active_user)
) -> UserDTO:
    """
    Require superadmin role
    Handles both uppercase (database) and lowercase (enum) role values
    """
    user_role = _extract_role_value(current_user.role)
    required_role = UserRole.SUPERADMIN.value  # 'superadmin'
    
    # Enhanced debugging
    settings = get_settings()
    if getattr(settings, 'debug', False):
        logger.debug(
            "require_superadmin check: user_id=%s, original_role='%s', normalized_role='%s', required_role='%s'", 
            getattr(current_user, 'id', 'unknown'), 
            current_user.role, 
            user_role, 
            required_role
        )
    
    if user_role != required_role:
        # Additional fallback check for is_superuser flag
        is_superuser = getattr(current_user, 'is_superuser', False)
        
        if is_superuser:
            if getattr(settings, 'debug', False):
                logger.debug("require_superadmin ALLOW via is_superuser flag")
            return current_user
        
        if getattr(settings, 'debug', False):
            logger.debug("require_superadmin DENY: role='%s', required='%s', is_superuser=%s", user_role, required_role, is_superuser)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "SUPERADMIN_REQUIRED", 
                "message": f"Superadmin privileges required. Current role: {current_user.role}"
            }
        )
    
    if getattr(settings, 'debug', False):
        logger.debug("require_superadmin ALLOW: role='%s'", user_role)
    return current_user


def require_role_hierarchy(minimum_role: UserRole):
    """
    Dependency factory for hierarchical role access control
    Users with higher roles can access lower role endpoints
    
    Usage:
        @router.get("/admin-or-higher")
        async def admin_endpoint(
            user: UserDTO = Depends(require_role_hierarchy(UserRole.ADMIN))
        ):
            pass
    """
    async def hierarchy_checker(
        current_user: UserDTO = Depends(get_current_active_user)
    ) -> UserDTO:
        role_value = _extract_role_value(current_user.role) or 'user'
        try:
            user_role = UserRole(role_value)
        except ValueError:
            user_role = UserRole.USER
        
        if not user_role.can_access_role(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_ROLE_LEVEL",
                    "message": f"Minimum role required: {minimum_role.value}. Current role: {user_role.value}"
                }
            )
        
        return current_user
    
    return hierarchy_checker