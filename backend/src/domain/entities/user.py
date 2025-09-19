"""
User Entity - Core Business Entity

Pure domain entity that represents a User in the system.
Maps to the existing users table but contains only business logic.
No framework dependencies - pure Python.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from ..value_objects.email import Email
from ..value_objects.password import Password
from ..value_objects.auth_method import AuthMethod, AuthMethodType
from ..value_objects.role import UserRole
from ..exceptions.domain_exceptions import (
    AccountDeactivatedException,
    AccountNotVerifiedException,
    ValidationError
)


@dataclass
class User:
    """
    User domain entity containing core business logic and rules.
    
    This entity maps to the existing users table but focuses purely on
    business behavior rather than persistence concerns.
    """
    
    # Identity
    id: Optional[int] = None
    email: Optional[Email] = None
    username: Optional[str] = None
    
    # Authentication
    password_hash: Optional[str] = None
    auth_method: Optional[AuthMethod] = None  # Track how user authenticates
    
    # Profile Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    
    # Account Status
    is_active: bool = True
    is_verified: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    
    # Role-Based Access Control
    role: UserRole = field(default_factory=UserRole.get_default_role)
    
    # Security Fields
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Localization
    timezone: str = "UTC"
    locale: str = "en"
    
    # Verification & Reset Tokens
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    
    # Audit Fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entity state after creation"""
        if self.email is None:
            raise ValidationError("User must have an email address")
        
        # Validate authentication method consistency
        if self.auth_method:
            if self.auth_method.is_password() and not self.password_hash:
                raise ValidationError("Password authentication method requires password_hash")
            elif self.auth_method.is_oauth() and self.password_hash:
                # OAuth users shouldn't have passwords, but we'll allow it for migration scenarios
                pass
    
    # Business Methods
    
    def change_password(self, new_password: Password) -> None:
        """
        Change user's password with business validation
        
        Args:
            new_password: New password value object
            
        Raises:
            AccountDeactivatedException: If account is deactivated
        """
        self._ensure_account_active()
        self.password_hash = new_password.hash()
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """
        Mark email as verified and clear verification token
        
        Raises:
            AccountDeactivatedException: If account is deactivated
        """
        self._ensure_account_active()
        self.is_verified = True
        self.email_verification_token = None
        self.email_verification_expires = None
        self.updated_at = datetime.utcnow()
    
    def deactivate_account(self) -> None:
        """
        Deactivate the user account
        
        Business rule: Deactivated accounts cannot perform actions
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def reactivate_account(self) -> None:
        """
        Reactivate a previously deactivated account
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        phone_number: Optional[str] = None,
        date_of_birth: Optional[datetime] = None
    ) -> None:
        """
        Update user profile information
        
        Args:
            first_name: User's first name
            last_name: User's last name  
            display_name: User's preferred display name
            bio: User's biography
            phone_number: User's phone number
            date_of_birth: User's date of birth
            
        Raises:
            AccountDeactivatedException: If account is deactivated
            ValidationError: If validation fails
        """
        self._ensure_account_active()
        
        # Validate inputs
        if first_name is not None:
            self._validate_name(first_name, "First name")
            self.first_name = first_name.strip()
        
        if last_name is not None:
            self._validate_name(last_name, "Last name")
            self.last_name = last_name.strip()
        
        if display_name is not None:
            self._validate_display_name(display_name)
            self.display_name = display_name.strip()
        
        if bio is not None:
            self._validate_bio(bio)
            self.bio = bio.strip() if bio else None
        
        if phone_number is not None:
            self._validate_phone_number(phone_number)
            self.phone_number = phone_number.strip() if phone_number else None
        
        if date_of_birth is not None:
            self._validate_date_of_birth(date_of_birth)
            self.date_of_birth = date_of_birth
        
        self.updated_at = datetime.utcnow()
    
    def set_verification_token(self, token: str, expires_at: datetime) -> None:
        """
        Set email verification token
        
        Args:
            token: Verification token
            expires_at: When token expires
        """
        self.email_verification_token = token
        self.email_verification_expires = expires_at
        self.updated_at = datetime.utcnow()
    
    def set_password_reset_token(self, token: str, expires_at: datetime) -> None:
        """
        Set password reset token
        
        Args:
            token: Reset token
            expires_at: When token expires
        """
        self.password_reset_token = token
        self.password_reset_expires = expires_at
        self.updated_at = datetime.utcnow()
    
    def clear_password_reset_token(self) -> None:
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        """
        Record successful login
        
        Raises:
            AccountDeactivatedException: If account is deactivated
            AccountNotVerifiedException: If email not verified
        """
        self._ensure_account_active()
        self._ensure_account_verified()
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def make_staff(self) -> None:
        """Grant staff privileges"""
        self.is_staff = True
        self.updated_at = datetime.utcnow()
    
    def remove_staff(self) -> None:
        """Remove staff privileges"""
        self.is_staff = False
        self.updated_at = datetime.utcnow()
    
    # Factory Methods
    
    @classmethod
    def create_with_password(
        cls,
        email: Email,
        password: Password,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[UserRole] = None,
        **kwargs
    ) -> "User":
        """
        Create a new user with password authentication
        
        Args:
            email: User email address
            password: User password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            role: User's role (defaults to USER)
            **kwargs: Additional user fields
            
        Returns:
            User entity with password authentication
        """
        user = cls(
            email=email,
            password_hash=password.hash(),
            auth_method=AuthMethod.password(),
            first_name=first_name,
            last_name=last_name,
            role=role or UserRole.get_default_role(),
            **kwargs
        )
        return user
    
    @classmethod
    def create_from_oauth(
        cls,
        email: Email,
        auth_method: AuthMethod,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_verified: bool = True,  # OAuth providers typically verify emails
        role: Optional[UserRole] = None,
        **kwargs
    ) -> "User":
        """
        Create a new user from OAuth authentication (no password required)
        
        Args:
            email: User email address
            auth_method: OAuth authentication method
            first_name: User's first name
            last_name: User's last name
            is_verified: Whether email is verified (default True for OAuth)
            role: User's role (defaults to USER)
            **kwargs: Additional user fields
            
        Returns:
            User entity with OAuth authentication (no password)
        """
        if not auth_method.is_oauth():
            raise ValidationError("create_from_oauth requires OAuth authentication method")
            
        user = cls(
            email=email,
            password_hash=None,  # OAuth users don't have passwords
            auth_method=auth_method,
            first_name=first_name,
            last_name=last_name,
            is_verified=is_verified,
            role=role or UserRole.get_default_role(),
            **kwargs
        )
        return user
    
    # Authentication Methods
    
    def can_login_with_password(self) -> bool:
        """Check if user can login with password"""
        return bool(
            self.auth_method and 
            self.auth_method.is_password() and 
            self.password_hash is not None
        )
    
    def can_login_with_oauth(self, provider: str) -> bool:
        """Check if user can login with specific OAuth provider"""
        return bool(
            self.auth_method and 
            self.auth_method.is_oauth() and
            str(self.auth_method.method_type).endswith(f"_{provider}_oauth")
        )
    
    # Role-Based Access Control Methods
    
    def assign_role(self, role: UserRole) -> None:
        """
        Assign a new role to the user
        
        Args:
            role: New role to assign
            
        Raises:
            AccountDeactivatedException: If account is deactivated
        """
        self._ensure_account_active()
        self.role = role
        self.updated_at = datetime.utcnow()
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if user has a specific role
        
        Args:
            role: Role to check
            
        Returns:
            True if user has the role
        """
        return self.role == role
    
    def has_any_role(self, roles: List[UserRole]) -> bool:
        """
        Check if user has any of the specified roles
        
        Args:
            roles: List of roles to check
            
        Returns:
            True if user has any of the roles
        """
        return self.role in roles
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            permission: Permission to check (e.g., "users:read")
            
        Returns:
            True if user has the permission
        """
        return self.role.has_permission(permission)
    
    def is_admin(self) -> bool:
        """Check if user is an admin (ADMIN or SUPERADMIN)"""
        return self.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    
    def is_superadmin(self) -> bool:
        """Check if user is a superadmin"""
        return self.role == UserRole.SUPERADMIN
    
    def can_manage_role(self, target_role: UserRole) -> bool:
        """
        Check if user can manage users with target role
        
        Args:
            target_role: Role to check management permissions for
            
        Returns:
            True if user can manage the target role
        """
        return self.role.can_access_role(target_role)
    
    def migrate_from_legacy_flags(self) -> None:
        """
        Migrate role from legacy is_staff/is_superuser flags
        This should be used during database migration
        """
        self.role = UserRole.from_legacy_flags(
            is_superuser=self.is_superuser,
            is_staff=self.is_staff
        )
        self.updated_at = datetime.utcnow()

    # Properties
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or "Unknown User"
    
    @property
    def name_for_display(self) -> str:
        """Get name for display (prefers display_name)"""
        return self.display_name or self.full_name
    
    @property
    def is_email_verification_token_valid(self) -> bool:
        """Check if email verification token is still valid"""
        if not self.email_verification_token or not self.email_verification_expires:
            return False
        return datetime.utcnow() < self.email_verification_expires
    
    @property
    def is_password_reset_token_valid(self) -> bool:
        """Check if password reset token is still valid"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.utcnow() < self.password_reset_expires
    
    @property
    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active and self.is_verified
    
    # Private helper methods
    
    def _ensure_account_active(self) -> None:
        """Ensure account is active before allowing operations"""
        if not self.is_active:
            raise AccountDeactivatedException()
    
    def _ensure_account_verified(self) -> None:
        """Ensure account is verified before allowing operations"""
        if not self.is_verified:
            raise AccountNotVerifiedException()
    
    def _validate_name(self, name: str, field_name: str) -> None:
        """Validate name fields"""
        if not name or not name.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        if len(name.strip()) > 100:
            raise ValidationError(f"{field_name} cannot exceed 100 characters")
        if not name.strip().replace(" ", "").replace("-", "").replace("'", "").isalpha():
            raise ValidationError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
    
    def _validate_display_name(self, display_name: str) -> None:
        """Validate display name"""
        if not display_name or not display_name.strip():
            raise ValidationError("Display name cannot be empty")
        if len(display_name.strip()) > 100:
            raise ValidationError("Display name cannot exceed 100 characters")
    
    def _validate_bio(self, bio: str) -> None:
        """Validate biography"""
        if bio and len(bio.strip()) > 500:
            raise ValidationError("Biography cannot exceed 500 characters")
    
    def _validate_phone_number(self, phone: str) -> None:
        """Validate phone number format"""
        if phone and len(phone.strip()) > 20:
            raise ValidationError("Phone number cannot exceed 20 characters")
        # Add more sophisticated phone validation if needed
    
    def _validate_date_of_birth(self, dob: datetime) -> None:
        """Validate date of birth"""
        if dob > datetime.utcnow():
            raise ValidationError("Date of birth cannot be in the future")
        
        # Check minimum age (13 years old)
        min_age_date = datetime.utcnow().replace(year=datetime.utcnow().year - 13)
        if dob > min_age_date:
            raise ValidationError("User must be at least 13 years old")
    
    def __str__(self) -> str:
        email_str = self.email.value if self.email else "No Email"
        return f"User(email={email_str}, name={self.name_for_display})"
    
    def __repr__(self) -> str:
        email_str = self.email.value if self.email else "No Email"
        return f"User(id={self.id}, email={email_str}, active={self.is_active})"