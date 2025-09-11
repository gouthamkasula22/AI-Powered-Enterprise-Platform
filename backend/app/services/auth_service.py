"""
Authentication Service

Core authentication business logic including user registration, login,
logout, and session management.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

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
from app.services.email_service import send_welcome_email, send_security_alert_email


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
            logger.info(f"Starting registration for email: {email}")
            
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            logger.info(f"Email {email} is available, proceeding with registration")
            
            # Hash password
            hashed_password = get_password_hash(password)
            logger.info(f"Password hashed successfully")
            
            # Generate email verification token
            email_verification_token = generate_random_token(32)
            verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # Create user
            user = User(
                email=email,
                password_hash=hashed_password,
                email_verification_token=email_verification_token,
                email_verification_expires=verification_expires
            )
            session.add(user)
            await session.flush()  # Get the user ID
            logger.info(f"User created with ID: {user.id}")
            
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
            logger.info("Password history entry created")
            
            # Create initial session
            device_fingerprint = generate_device_fingerprint(user_agent, ip_address)
            current_time = datetime.utcnow()
            user_session = UserSession(
                user_id=user.id,
                session_token=generate_random_token(32),
                device_fingerprint=device_fingerprint,
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True,
                expires_at=current_time + timedelta(days=30),
                last_accessed=current_time,
                login_method="password"
            )
            session.add(user_session)
            await session.flush()  # Get the session ID
            logger.info(f"User session created with ID: {user_session.id}")
            
            # Log registration in login history
            await AuthenticationService._log_login_attempt(
                session=session,
                user_id=user.id,
                session_id=user_session.id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                login_type="password",
                result="success",
                failure_reason=None,
                start_time=current_time
            )
            logger.info("Login history entry created")
            
            # Commit the transaction
            await session.commit()
            logger.info(f"User registration completed successfully for {email}")
            
            # Send welcome email with verification link
            try:
                await send_welcome_email(
                    user_email=email,
                    user_name=email.split('@')[0],  # Use email prefix as name for now
                    verification_token=email_verification_token
                )
                logger.info(f"Welcome email sent successfully to {email}")
            except Exception as email_error:
                logger.error(f"Failed to send welcome email to {email}: {str(email_error)}")
                # Don't fail registration if email fails - user is already created
            
            # Create JWT tokens for the new user
            access_token = create_access_token(subject=str(user.id))
            refresh_token = create_refresh_token(subject=str(user.id))
            
            return {
                "message": "User registered successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                    "created_at": user.created_at
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
            logger.error(f"Registration failed for {email}: {str(e)}")
            logger.exception("Full exception details:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to server error"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def verify_email(verification_token: str) -> Dict[str, Any]:
        """
        Verify user's email address using verification token
        
        Args:
            verification_token: Email verification token
            
        Returns:
            Dictionary with verification result
            
        Raises:
            HTTPException: If verification fails
        """
        session = await get_db_session()
        try:
            # Find user with verification token
            result = await session.execute(
                select(User).where(
                    User.email_verification_token == verification_token
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification token"
                )
            
            # Check if token has expired
            if user.email_verification_expires and user.email_verification_expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token has expired"
                )
            
            # Check if already verified
            if user.is_verified:
                return {
                    "message": "Email already verified",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "is_verified": True
                    }
                }
            
            # Verify the email
            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            
            await session.commit()
            
            return {
                "message": "Email verified successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_verified": True
                }
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed due to server error"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def resend_verification_email(email: str) -> Dict[str, Any]:
        """
        Resend email verification link
        
        Args:
            email: User email address
            
        Returns:
            Dictionary with resend result
            
        Raises:
            HTTPException: If resend fails
        """
        session = await get_db_session()
        try:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if already verified
            if user.is_verified:
                return {
                    "message": "Email is already verified"
                }
            
            # Generate new verification token
            new_token = generate_random_token(32)
            verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # Update user with new token
            user.email_verification_token = new_token
            user.email_verification_expires = verification_expires
            
            await session.commit()
            
            # Send verification email
            try:
                await send_welcome_email(
                    user_email=user.email,
                    user_name=user.email.split('@')[0],
                    verification_token=new_token
                )
                logger.info(f"Verification email resent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to resend verification email to {user.email}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email"
                ) from e
            
            return {
                "message": "Verification email has been resent. Please check your inbox."
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend verification email"
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
            
            # Check password against password history first, then fallback to user.password_hash
            password_hash_to_check = None
            if password_record:
                password_hash_to_check = password_record.password_hash
            elif user.password_hash:
                password_hash_to_check = user.password_hash
                logger.warning(f"No password history found for user {user.id}, using direct password hash")
            
            if not password_hash_to_check or not verify_password(password, password_hash_to_check):
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
            
            # Check for new device/location and send security alert
            try:
                is_new_device = await AuthenticationService._is_new_device_or_location(
                    user.id, device_fingerprint, ip_address, session
                )
                
                if is_new_device:
                    await send_security_alert_email(
                        user_email=user.email,
                        user_name=user.email.split('@')[0],
                        alert_type="new_login",
                        details={
                            "ip_address": ip_address,
                            "user_agent": user_agent,
                            "timestamp": datetime.utcnow().isoformat(),
                            "device_fingerprint": device_fingerprint[:16] + "...",  # Partial for privacy
                            "location": "Unknown",  # Could be enhanced with IP geolocation
                            "action": "New device login detected"
                        }
                    )
                    logger.info(f"Security alert sent for new device login: {user.email}")
            except Exception as e:
                logger.error(f"Failed to send security alert for {user.email}: {str(e)}")
                # Don't fail login if security alert fails
            
            return {
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
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
    async def request_password_reset(email: str, ip_address: str) -> Dict[str, Any]:
        """
        Generate password reset token and send reset email
        
        Args:
            email: User email address
            ip_address: Client IP address for logging
            
        Returns:
            Dictionary with reset request confirmation
            
        Raises:
            HTTPException: If user not found or email sending fails
        """
        session = await get_db_session()
        try:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists - security best practice
                return {
                    "message": "If an account with that email exists, a password reset link has been sent."
                }
            
            # Generate reset token (expires in 1 hour)
            reset_token = generate_random_token(32)
            reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            
            # Update user with reset token
            user.password_reset_token = reset_token
            user.password_reset_expires = reset_expires
            
            await session.commit()
            
            # Send password reset email
            try:
                from app.services.email_service import send_password_reset_email
                await send_password_reset_email(
                    user_email=user.email,
                    user_name=user.email.split('@')[0],
                    reset_token=reset_token
                )
                logger.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send password reset email"
                ) from e
            
            return {
                "message": "If an account with that email exists, a password reset link has been sent."
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Password reset request failed for {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset request failed"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def reset_password(token: str, new_password: str, ip_address: str) -> Dict[str, Any]:
        """
        Reset password using reset token
        
        Args:
            token: Password reset token
            new_password: New password
            ip_address: Client IP address for logging
            
        Returns:
            Dictionary with reset confirmation and user info
            
        Raises:
            HTTPException: If token is invalid or reset fails
        """
        logger.info(f"reset_password called with token: {token[:10] if token else 'None'}...")
        session = await get_db_session()
        try:
            # Find user with reset token
            result = await session.execute(
                select(User).where(User.password_reset_token == token)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Check if token has expired
            if user.password_reset_expires and user.password_reset_expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired"
                )
            
            # Validate new password
            logger.info("Validating password strength...")
            password_validation = validate_password_strength(new_password)
            logger.info(f"Password validation result: {password_validation}")
            if not password_validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password does not meet security requirements"
                )
            
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            # Update user password and clear reset token
            user.password_hash = hashed_password
            user.password_reset_token = None
            user.password_reset_expires = None
            user.updated_at = datetime.utcnow()
            
            # Create password history entry
            password_history = PasswordHistory(
                user_id=user.id,
                password_hash=hashed_password,
                strength_score=password_validation["strength_score"] / 100.0,
                length=len(new_password),
                has_uppercase=password_validation["requirements"]["uppercase"],
                has_lowercase=password_validation["requirements"]["lowercase"],
                has_digits=password_validation["requirements"]["digit"],
                has_symbols=password_validation["requirements"]["special"],
                policy_compliant=True,
                set_at=datetime.utcnow(),
                change_reason="password_reset",
                ip_address=ip_address
            )
            session.add(password_history)
            
            await session.commit()
            
            # Send security alert email
            try:
                await send_security_alert_email(
                    user_email=user.email,
                    user_name=user.email.split('@')[0],
                    alert_type="password_reset",
                    details={
                        "ip_address": ip_address,
                        "user_agent": "Password Reset",
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "Password was reset"
                    }
                )
                logger.info(f"Security alert sent for password reset: {user.email}")
            except Exception as e:
                logger.error(f"Failed to send security alert for password reset: {str(e)}")
                # Don't fail the reset if security email fails
            
            return {
                "message": "Password reset successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at
                }
            }
            
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Password reset failed for token {token[:10]}...: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed"
            ) from e
        finally:
            await session.close()
    
    @staticmethod
    async def validate_reset_token(token: str) -> Dict[str, Any]:
        """
        Validate password reset token
        
        Args:
            token: Password reset token to validate
            
        Returns:
            Dictionary with validation result
            
        Raises:
            HTTPException: If validation fails
        """
        session = await get_db_session()
        try:
            # Find user with reset token
            result = await session.execute(
                select(User).where(User.password_reset_token == token)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return {
                    "is_valid": False,
                    "message": "Invalid reset token",
                    "email": None
                }
            
            # Check if token has expired
            if user.password_reset_expires and user.password_reset_expires < datetime.now(timezone.utc):
                return {
                    "is_valid": False,
                    "message": "Reset token has expired",
                    "email": None
                }
            
            return {
                "is_valid": True,
                "message": "Reset token is valid",
                "email": user.email
            }
            
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token validation failed"
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
    
    @staticmethod
    async def _is_new_device_or_location(
        user_id: uuid.UUID,
        device_fingerprint: str,
        ip_address: str,
        session: AsyncSession
    ) -> bool:
        """
        Check if this is a new device or location for the user
        
        Args:
            user_id: User UUID
            device_fingerprint: Browser/device fingerprint
            ip_address: Client IP address
            session: Database session
            
        Returns:
            True if new device/location, False otherwise
        """
        try:
            # Check if we've seen this device fingerprint for this user before
            recent_cutoff = datetime.utcnow() - timedelta(days=30)  # Check last 30 days
            
            result = await session.execute(
                select(LoginHistory).where(
                    and_(
                        LoginHistory.user_id == user_id,
                        LoginHistory.result == "success",
                        LoginHistory.created_at >= recent_cutoff,
                        or_(
                            LoginHistory.user_agent.contains(device_fingerprint[:50]),  # Partial match
                            LoginHistory.ip_address == ip_address
                        )
                    )
                ).limit(1)
            )
            
            existing_login = result.scalar_one_or_none()
            
            # If no recent successful login from this device/IP, consider it new
            return existing_login is None
            
        except Exception as e:
            logger.error(f"Error checking device/location for user {user_id}: {str(e)}")
            # Default to treating as new device for security
            return True
    
    @staticmethod
    async def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User UUID
            
        Returns:
            User object if found, None otherwise
        """
        session = await get_db_session()
        try:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None
        finally:
            await session.close()
