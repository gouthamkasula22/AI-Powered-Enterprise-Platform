"""
User Repository Implementation

Implements the IUserRepository interface using SQLAlchemy and PostgreSQL.
This provides the concrete implementation for user data access.
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# Import domain components
from ...domain.entities.user import User
from ...domain.repositories.user_repository import IUserRepository
from ...domain.value_objects.email import Email
from ...domain.value_objects.role import UserRole
from ...domain.value_objects.password import Password
from ...domain.value_objects.auth_method import AuthMethod, AuthMethodType
from ...domain.exceptions.domain_exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    RepositoryError
)

# Import infrastructure components
from .models import UserModel

from .models import UserModel


class SqlUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of the User Repository.
    
    This class handles all database operations for users,
    converting between domain entities and database models.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, user: User) -> User:
        """Save a user to the database"""
        try:
            if user.id is None:
                # Create new user using INSERT with explicit role
                role_value = user.role.value if user.role else 'USER'
                auth_method_str = user.auth_method.method_type.value if user.auth_method else 'PASSWORD'
                auth_provider_id = user.auth_method.provider_id if user.auth_method else None
                
                # Use raw INSERT to explicitly include role
                from sqlalchemy import text
                result = await self.session.execute(
                    text("""
                        INSERT INTO users (
                            email, password_hash, auth_method, auth_provider_id,
                            username, first_name, last_name, display_name,
                            profile_picture_url, bio, phone_number, date_of_birth,
                            is_active, is_verified, is_staff, is_superuser,
                            role, failed_login_attempts, timezone, locale,
                            email_verification_token, email_verification_expires_at,
                            password_reset_token, password_reset_expires_at,
                            created_at, updated_at, last_login
                        ) VALUES (
                            :email, :password_hash, :auth_method, :auth_provider_id,
                            :username, :first_name, :last_name, :display_name,
                            :profile_picture_url, :bio, :phone_number, :date_of_birth,
                            :is_active, :is_verified, :is_staff, :is_superuser,
                            :role, :failed_login_attempts, :timezone, :locale,
                            :email_verification_token, :email_verification_expires_at,
                            :password_reset_token, :password_reset_expires_at,
                            :created_at, :updated_at, :last_login
                        ) RETURNING id
                    """),
                    {
                        'email': user.email.value if user.email else None,
                        'password_hash': user.password_hash,
                        'auth_method': auth_method_str,
                        'auth_provider_id': auth_provider_id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'display_name': user.display_name,
                        'profile_picture_url': user.profile_picture_url,
                        'bio': user.bio,
                        'phone_number': user.phone_number,
                        'date_of_birth': user.date_of_birth,
                        'is_active': user.is_active,
                        'is_verified': user.is_verified,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'role': role_value,
                        'failed_login_attempts': 0,
                        'timezone': 'UTC',
                        'locale': 'en',
                        'email_verification_token': user.email_verification_token,
                        'email_verification_expires_at': user.email_verification_expires,
                        'password_reset_token': user.password_reset_token,
                        'password_reset_expires_at': user.password_reset_expires,
                        'created_at': user.created_at,
                        'updated_at': user.updated_at,
                        'last_login': user.last_login
                    }
                )
                user.id = result.scalar()  # type: ignore
            else:
                # Update existing user - exclude role field that SQLAlchemy doesn't recognize
                update_data = self._domain_to_dict(user)
                # Remove problematic fields that SQLAlchemy can't handle
                update_data.pop('role', None)
                
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user.id)
                    .values(**update_data)
                )
                await self.session.execute(stmt)
            
            await self.session.commit()
            return user
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Database integrity error details: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            if hasattr(e, 'orig'):
                logger.error(f"Original error: {e.orig}")
            
            if "email" in str(e):
                email_value = user.email.value if user.email else "unknown"
                raise UserAlreadyExistsError(f"User with email {email_value} already exists")
            raise RepositoryError(f"Database integrity error: {e}")
        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to save user: {e}")
    
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by ID"""
        try:
            # Use raw SQL to ensure ALL columns (including role) are fetched.
            # The ORM-generated SELECT previously omitted the role column in this environment,
            # causing role to default to USER in _model_to_domain.
            from sqlalchemy import text
            result = await self.session.execute(
                text("SELECT * FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.first()
            if not row:
                return None
            return self._raw_row_to_domain(row)
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by ID: {e}")
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find a user by email"""
        try:
            # Use raw SQL to ensure ALL columns including role are fetched
            from sqlalchemy import text
            result = await self.session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email.value}
            )
            row = result.first()
            
            if not row:
                return None
                
            # Convert raw row to User domain entity
            return self._raw_row_to_domain(row)
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by email: {e}")
    
    async def _fetch_user_role(self, user_id: int) -> Optional[str]:
        """Fetch user role directly from database to work around SQLAlchemy metadata issues"""
        try:
            from sqlalchemy import text
            result = await self.session.execute(
                text("SELECT role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.first()
            return row[0] if row else None
        except Exception:
            return None
    
    def _raw_row_to_domain(self, row) -> User:
        """Convert database row to domain entity (for raw SQL queries)"""
        # Convert auth_method string back to AuthMethod object
        auth_method = None
        if row.auth_method:
            auth_method_str = str(row.auth_method)
            provider_id = str(row.auth_provider_id) if row.auth_provider_id else None
            
            try:
                if auth_method_str == "password" or auth_method_str == "PASSWORD":
                    auth_method = AuthMethod.password()
                elif auth_method_str == "google_oauth":
                    if provider_id:
                        auth_method = AuthMethod.google_oauth(provider_id)
                elif auth_method_str == "github_oauth":
                    if provider_id:
                        auth_method = AuthMethod.github_oauth(provider_id)
                else:
                    auth_method = AuthMethod.password()
            except Exception:
                auth_method = None
        
        # Convert role string to UserRole enum - THIS IS THE KEY FIX
        user_role = UserRole.USER  # Default role
        if hasattr(row, 'role') and row.role:
            try:
                # Database stores uppercase (ADMIN) but enum expects lowercase (admin)
                role_value = str(row.role).lower()
                user_role = UserRole(role_value)
            except ValueError:
                user_role = UserRole.USER
        
        return User(
            id=row.id,
            email=Email(row.email) if row.email else None,
            username=row.username,
            password_hash=row.password_hash,
            auth_method=auth_method,
            role=user_role,  # Direct assignment since we're creating new User
            first_name=row.first_name,
            last_name=row.last_name,
            display_name=row.display_name,
            profile_picture_url=row.profile_picture_url,
            bio=row.bio,
            phone_number=row.phone_number,
            date_of_birth=row.date_of_birth,
            is_active=row.is_active,
            is_verified=row.is_verified,
            email_verification_token=row.email_verification_token,
            email_verification_expires=row.email_verification_expires_at,
            password_reset_token=row.password_reset_token,
            password_reset_expires=row.password_reset_expires_at,
            is_staff=row.is_staff,
            is_superuser=row.is_superuser,
            failed_login_attempts=row.failed_login_attempts,
            locked_until=row.locked_until,
            last_login=row.last_login,
            timezone=row.timezone,
            locale=row.locale,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username"""
        try:
            stmt = select(UserModel).where(
                UserModel.username == username
            )
            result = await self.session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return self._model_to_domain(user_model) if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by username: {e}")
    
    async def find_by_email_verification_token(self, token: str) -> Optional[User]:
        """Find a user by email verification token"""
        try:
            stmt = select(UserModel).where(
                UserModel.email_verification_token == token
            )
            result = await self.session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return self._model_to_domain(user_model) if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by verification token: {e}")
    
    async def find_by_password_reset_token(self, token: str) -> Optional[User]:
        """Find a user by password reset token"""
        try:
            stmt = select(UserModel).where(
                UserModel.password_reset_token == token
            )
            result = await self.session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            return self._model_to_domain(user_model) if user_model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by reset token: {e}")
    
    async def list_users(self, limit: int = 100, offset: int = 0,
                         include_inactive: bool = False) -> List[User]:
        """List users with pagination.

        Uses raw SQL to guarantee the `role` column (and any newly added columns)
        are always selected. Mirrors the fix applied in `find_by_id` / `find_by_email`.
        """
        try:
            from sqlalchemy import text
            if include_inactive:
                sql = text("""
                    SELECT * FROM users
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {"limit": limit, "offset": offset}
            else:
                sql = text("""
                    SELECT * FROM users
                    WHERE is_active = true
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {"limit": limit, "offset": offset}

            result = await self.session.execute(sql, params)
            rows = result.fetchall()
            users: List[User] = []
            for row in rows:
                try:
                    users.append(self._raw_row_to_domain(row))
                except Exception as conv_err:
                    # Skip problematic row but continue returning others
                    logger.warning(f"Failed to convert user row id={getattr(row, 'id', 'unknown')}: {conv_err}")
                    continue
            return users
        except Exception as e:
            raise RepositoryError(f"Failed to list users: {e}")
    
    async def find_all(self) -> List[User]:
        """Find all users without pagination"""
        try:
            stmt = select(UserModel).order_by(UserModel.created_at.desc())
            result = await self.session.execute(stmt)
            user_models = result.scalars().all()
            
            users = []
            for model in user_models:
                try:
                    user = self._model_to_domain(model)
                    users.append(user)
                except Exception as e:
                    print(f"Error converting user model {model.id}: {e}")
                    continue
            
            return users
            
        except Exception as e:
            print(f"Failed to find all users: {e}")
            raise RepositoryError(f"Failed to find all users: {e}")
    
    async def delete(self, user_id: int) -> bool:
        """Soft delete a user"""
        try:
            stmt = (
                update(UserModel)
                .where(
                    UserModel.id == user_id,
                    UserModel
                )
                .values(is_active=False)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to delete user: {e}")
    
    def _domain_to_model(self, user: User) -> UserModel:
        """Convert domain entity to database model"""
        # Convert AuthMethod to string representation
        auth_method_str = None
        auth_provider_id = None
        if user.auth_method:
            auth_method_str = str(user.auth_method.method_type.value)
            auth_provider_id = user.auth_method.provider_id
        
        # Create a dictionary of parameters
        model_params = {
            "email": user.email.value if user.email else None,
            "username": user.username,
            "password_hash": user.password_hash,
            "auth_method": auth_method_str or 'PASSWORD',  # Default required
            "auth_provider_id": auth_provider_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "profile_picture_url": user.profile_picture_url,
            "bio": user.bio,
            "phone_number": user.phone_number,
            "date_of_birth": user.date_of_birth,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "email_verification_token": user.email_verification_token,
            "email_verification_expires": user.email_verification_expires,
            "password_reset_token": user.password_reset_token,
            "password_reset_expires": user.password_reset_expires,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "role": user.role.value if user.role else 'user',  # Consistent with other fields
            "last_login": user.last_login,
            "timezone": user.timezone or 'UTC',
            "locale": user.locale or 'en',
            "failed_login_attempts": getattr(user, 'failed_login_attempts', 0)
        }
        
        # Add created_at and updated_at if they exist
        if user.created_at:
            model_params["created_at"] = user.created_at
        if user.updated_at:
            model_params["updated_at"] = user.updated_at
            
        # Create model with all required fields using kwargs
        model = UserModel(**model_params)
        
        return model
    
    def _domain_to_dict(self, user: User) -> dict:
        """Convert domain entity to dictionary for updates"""
        # Convert AuthMethod to string representation
        auth_method_str = None
        auth_provider_id = None
        if user.auth_method:
            auth_method_str = str(user.auth_method.method_type.value)
            auth_provider_id = user.auth_method.provider_id
        
        return {
            "email": user.email.value if user.email else None,
            "username": user.username,
            "password_hash": user.password_hash,
            "auth_method": auth_method_str,
            "auth_provider_id": auth_provider_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "profile_picture_url": user.profile_picture_url,
            "bio": user.bio,
            "phone_number": user.phone_number,
            "date_of_birth": user.date_of_birth,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "email_verification_token": user.email_verification_token,
            "email_verification_expires_at": user.email_verification_expires,  # Note: _at suffix
            "password_reset_token": user.password_reset_token,
            "password_reset_expires_at": user.password_reset_expires,  # Note: _at suffix
            # Include security fields now that they exist in DB
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "role": user.role.value if user.role else 'USER',
            "last_login": user.last_login,
            "timezone": user.timezone,
            "locale": user.locale,
            "updated_at": datetime.utcnow()
        }
    
    def _model_to_domain(self, model: UserModel) -> User:
        """Convert database model to domain entity"""
        # Convert auth_method string back to AuthMethod object
        auth_method = None
        if model.auth_method:  # type: ignore
            auth_method_str = str(model.auth_method)  # type: ignore
            provider_id = str(model.auth_provider_id) if model.auth_provider_id else None  # type: ignore
            
            try:
                if auth_method_str == "password":
                    auth_method = AuthMethod.password()
                elif auth_method_str == "google_oauth":
                    auth_method = AuthMethod.google_oauth(provider_id or "")
                elif auth_method_str == "github_oauth":
                    auth_method = AuthMethod.github_oauth(provider_id or "")
                else:
                    # Default to password for unknown methods
                    auth_method = AuthMethod.password()
            except Exception:
                # If AuthMethod creation fails, default to None
                auth_method = None
        
        # Type checker has issues with SQLAlchemy mapped attributes, use type ignore where needed
        # Convert role string to UserRole enum
        user_role = UserRole.USER  # Default role
        if hasattr(model, 'role') and model.role:  # type: ignore
            try:
                # Handle both uppercase and lowercase role values from database
                role_value = str(model.role).lower()  # type: ignore
                user_role = UserRole(role_value)
            except ValueError:
                user_role = UserRole.USER  # Default to USER if conversion fails
        
        return User(
            id=model.id,  # type: ignore
            email=Email(model.email) if model.email else None,  # type: ignore
            username=model.username,  # type: ignore
            password_hash=model.password_hash,  # type: ignore
            auth_method=auth_method,
            role=user_role,
            first_name=model.first_name,  # type: ignore
            last_name=model.last_name,  # type: ignore
            display_name=model.display_name,  # type: ignore
            profile_picture_url=model.profile_picture_url,  # type: ignore
            bio=model.bio,  # type: ignore
            phone_number=model.phone_number,  # type: ignore
            date_of_birth=model.date_of_birth,  # type: ignore
            is_active=model.is_active,  # type: ignore
            is_verified=model.is_verified,  # type: ignore
            email_verification_token=model.email_verification_token,  # type: ignore
            email_verification_expires=getattr(model, 'email_verification_expires_at', None),
            password_reset_token=model.password_reset_token,  # type: ignore
            password_reset_expires=getattr(model, 'password_reset_expires_at', None),
            is_staff=model.is_staff,  # type: ignore
            is_superuser=model.is_superuser,  # type: ignore
            failed_login_attempts=getattr(model, 'failed_login_attempts', 0),
            locked_until=getattr(model, 'locked_until', None),
            last_login=model.last_login,  # type: ignore
            timezone=str(getattr(model, 'timezone', 'UTC')) if hasattr(model, 'timezone') and getattr(model, 'timezone') is not None else "UTC",
            locale=str(getattr(model, 'locale', 'en')) if hasattr(model, 'locale') and getattr(model, 'locale') is not None else "en",
            created_at=model.created_at,  # type: ignore
            updated_at=model.updated_at  # type: ignore
        )
    
    # Add missing interface methods
    
    async def find_by_verification_token(self, token: str) -> Optional[User]:
        """Find user by email verification token (alias)"""
        return await self.find_by_email_verification_token(token)
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        user.id = None  # Ensure it's a new user
        return await self.save(user)
    
    async def update(self, user: User) -> User:
        """Update existing user"""
        if user.id is None:
            raise RepositoryError("Cannot update user without ID")
        return await self.save(user)
    
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists with given email"""
        user = await self.find_by_email(email)
        return user is not None
    
    async def find_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Find active users with pagination"""
        try:
            stmt = (
                select(UserModel)
                .where(
                    UserModel,
                    UserModel.is_active == True
                )
                .offset(offset)
                .limit(limit)
                .order_by(UserModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find active users: {e}")
    
    async def find_unverified_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Find unverified users with pagination"""
        try:
            stmt = (
                select(UserModel)
                .where(
                    UserModel,
                    UserModel.is_verified == False
                )
                .offset(offset)
                .limit(limit)
                .order_by(UserModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in user_models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find unverified users: {e}")
    
    async def count_total_users(self) -> int:
        """Count total number of users"""
        try:
            stmt = select(func.count(UserModel.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to count total users: {e}")
    
    async def count_active_users(self) -> int:
        """Count active users"""
        try:
            stmt = select(func.count(UserModel.id)).where(
                UserModel,
                UserModel.is_active == True
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to count active users: {e}")