"""
Authentication Service

Core authentication business logic including user registration, login,
logout, and session management.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    validate_password_strength,
    generate_device_fingerprint,
    generate_random_token
)
from app.models import User, UserSession, LoginHistory, PasswordHistory
from app.core.database import get_db_session


class AuthenticationService:
    """Main authentication service handling user authentication operations"""
    
    @staticmethod
    async def register_user(
        email: str, 
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            email: User email address
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with user info and tokens
            
        Raises:
            HTTPException: If registration fails
        """
        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        session = await get_db_session()
        try:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Hash password
            hashed_password = get_password_hash(password)
            
            # Create user
            user = User(email=email)
            session.add(user)
            await session.flush()  # Get the user ID
            
            # Create password history entry
            password_history = PasswordHistory(
                user_id=user.id,
                password_hash=hashed_password,
                strength_score=password_validation["strength_score"] / 100.0,
                length=len(password),
                has_uppercase=password_validation["requirements"]["uppercase"],
                has_lowercase=password_validation["requirements"]["lowercase"],
                has_digits=password_validation["requirements"]["digit"],
                has_symbols=password_validation["requirements"]["special"],
                policy_compliant=True,
                set_at=datetime.utcnow(),
                change_reason="initial_registration",
                ip_address=ip_address
            )
            session.add(password_history)
            
            # Create tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = create_refresh_token(subject=str(user.id))
            
            # Generate device fingerprint
            device_fingerprint = generate_device_fingerprint(user_agent, ip_address)
            
            # Create user session
            user_session = UserSession(
                user_id=user.id,
                session_token=generate_random_token(32),
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                expires_at=datetime.utcnow() + timedelta(days=7),
                last_accessed=datetime.utcnow(),
                is_active=True,
                login_method="email_password"
            )
            session.add(user_session)
            
            # Log registration in login history
            login_history = LoginHistory(
                user_id=user.id,
                session_id=user_session.id,
                email_attempted=email,
                ip_address=ip_address,
                user_agent=user_agent,
                login_type="password",
                result="success",
                duration_ms=0  # Registration is instant
            )
            session.add(login_history)
            
            await session.commit()
            
            return {
                "message": "User registered successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat()
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to server error"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def authenticate_user(
        email: str, 
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email address
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with user info and tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        login_start_time = datetime.utcnow()
        session = await get_db_session()
        
        try:
            # Find user by email
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                # Log failed attempt
                await AuthenticationService._log_login_attempt(
                    session, None, None, email, ip_address, user_agent, 
                    "password", "failure", "user_not_found", login_start_time
                )
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Get user's current password hash
            password_result = await session.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(1)
            )
            password_record = password_result.scalar_one_or_none()
            
            if not password_record or not verify_password(password, password_record.password_hash):
                # Log failed attempt
                await AuthenticationService._log_login_attempt(
                    session, user.id, None, email, ip_address, user_agent,
                    "password", "failure", "invalid_password", login_start_time
                )
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Create tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = create_refresh_token(subject=str(user.id))
            
            # Generate device fingerprint
            device_fingerprint = generate_device_fingerprint(user_agent, ip_address)
            
            # Create user session
            user_session = UserSession(
                user_id=user.id,
                session_token=generate_random_token(32),
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                expires_at=datetime.utcnow() + timedelta(days=7),
                last_accessed=datetime.utcnow(),
                is_active=True,
                login_method="email_password"
            )
            session.add(user_session)
            await session.flush()  # Get session ID
            
            # Log successful login
            await AuthenticationService._log_login_attempt(
                session, user.id, user_session.id, email, ip_address, user_agent,
                "password", "success", None, login_start_time
            )
            
            await session.commit()
            
            return {
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat()
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed due to server error"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def _log_login_attempt(
        session: AsyncSession,
        user_id: Optional[uuid.UUID],
        session_id: Optional[uuid.UUID],
        email: str,
        ip_address: str,
        user_agent: str,
        login_type: str,
        result: str,
        failure_reason: Optional[str],
        start_time: datetime
    ):
        """Log login attempt to login history"""
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        login_history = LoginHistory(
            user_id=user_id,
            session_id=session_id,
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            login_type=login_type,
            result=result,
            failure_reason=failure_reason,
            duration_ms=duration_ms
        )
        session.add(login_history)
