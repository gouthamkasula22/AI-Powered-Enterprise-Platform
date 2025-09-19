"""
Commands - Write Operations

Commands represent write operations that change the system state.
They follow the Command pattern and contain all data needed for the operation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Command:
    """Base command class"""
    pass


# Authentication Commands
@dataclass
class RegisterUserCommand(Command):
    """Command to register a new user"""
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


@dataclass
class LoginUserCommand(Command):
    """Command to login a user"""
    email: str
    password: str
    remember_me: bool = False


@dataclass
class RefreshTokenCommand(Command):
    """Command to refresh authentication tokens"""
    refresh_token: str


@dataclass
class LogoutCommand(Command):
    """Command to logout a user"""
    access_token: str


@dataclass
class LogoutAllCommand(Command):
    """Command to logout user from all devices"""
    user_id: int


# Password Management Commands
@dataclass
class InitiatePasswordResetCommand(Command):
    """Command to initiate password reset process"""
    email: str


@dataclass
class ConfirmPasswordResetCommand(Command):
    """Command to confirm password reset with token"""
    token: str
    new_password: str


@dataclass
class ChangePasswordCommand(Command):
    """Command to change user password"""
    user_id: int
    current_password: str
    new_password: str


# Email Verification Commands
@dataclass
class SendVerificationEmailCommand(Command):
    """Command to send email verification"""
    user_id: int


@dataclass
class VerifyEmailCommand(Command):
    """Command to verify email with token"""
    token: str


# Profile Management Commands
@dataclass
class UpdateProfileCommand(Command):
    """Command to update user profile"""
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


@dataclass
class UpdateProfilePictureCommand(Command):
    """Command to update profile picture"""
    user_id: int
    profile_picture_url: str


@dataclass
class DeactivateAccountCommand(Command):
    """Command to deactivate user account"""
    user_id: int


@dataclass
class ReactivateAccountCommand(Command):
    """Command to reactivate user account"""
    user_id: int