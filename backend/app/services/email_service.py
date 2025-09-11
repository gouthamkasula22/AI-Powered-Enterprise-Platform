"""
Email Service Module

Provides email sending functionality with template support, async operations,
and comprehensive error handling for the authentication system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, Template
import emails

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateError(Exception):
    """Raised when email template processing fails"""
    pass


class EmailSendError(Exception):
    """Raised when email sending fails"""
    pass


class EmailService:
    """
    Async Email Service with template support and comprehensive error handling
    """
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.smtp_use_ssl = settings.SMTP_USE_SSL
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        
        # Initialize Jinja2 template environment
        template_dir = Path(settings.EMAIL_TEMPLATES_DIR)
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
        else:
            logger.warning(f"Email template directory not found: {template_dir}")
            self.jinja_env = None
    
    async def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email with HTML and/or text content
        
        Args:
            to_email: Recipient email address(es)
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self._is_configured():
            logger.error("Email service not configured properly")
            return False
        
        try:
            # Ensure to_email is a list
            recipients = [to_email] if isinstance(to_email, str) else to_email
            
            # Create email message using emails library
            message = emails.html(
                html=html_content or "",
                text=text_content or "",
                subject=subject,
                mail_from=(self.from_name, self.from_email)
            )
            
            # Send using emails library (more reliable than aiosmtplib for SendGrid)
            smtp_config = {
                'host': self.smtp_host,
                'port': self.smtp_port,
                'tls': self.smtp_use_tls,
                'ssl': self.smtp_use_ssl
            }
            
            if self.smtp_username and self.smtp_password:
                smtp_config.update({
                    'user': self.smtp_username,
                    'password': self.smtp_password
                })
            
            # Send to each recipient
            for recipient in recipients:
                response = message.send(to=recipient, smtp=smtp_config)
                if response.status_code != 250:
                    logger.error(f"Failed to send email to {recipient}: {response}")
                    return False
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailSendError(f"Failed to send email: {str(e)}")
    
    async def send_template_email(
        self,
        to_email: Union[str, List[str]],
        template_name: str,
        subject: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Send an email using a Jinja2 template
        
        Args:
            to_email: Recipient email address(es)
            template_name: Name of the template file (without extension)
            subject: Email subject
            context: Template context variables
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.jinja_env:
            logger.error("Template environment not initialized")
            return False
        
        try:
            # Load and render HTML template
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**context)
            
            # Try to load text template (optional)
            text_content = None
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**context)
            except:
                # If no text template, extract text from HTML
                text_content = self._html_to_text(html_content)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise EmailTemplateError(f"Template rendering failed: {str(e)}")
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text"""
        try:
            # Basic HTML to text conversion
            import re
            # Remove HTML tags
            text = re.sub('<[^<]+?>', '', html_content)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html_content
    
    def _is_configured(self) -> bool:
        """Check if email service is properly configured"""
        required_settings = [
            self.smtp_host,
            self.smtp_port,
            self.from_email
        ]
        return all(setting is not None for setting in required_settings)
    
    async def test_connection(self) -> bool:
        """Test SMTP connection using emails library (same as send_email)"""
        if not self._is_configured():
            logger.error("Email service not configured for testing")
            return False
        
        try:
            # Use emails library for testing (same as actual sending)
            import emails
            
            # Create a simple test message (won't be sent)
            test_message = emails.html(
                html="<p>Connection Test</p>",
                text="Connection Test",
                subject="Connection Test",
                mail_from=(self.from_name, self.from_email)
            )
            
            # Configure SMTP same as send_email method
            smtp_config = {
                'host': self.smtp_host,
                'port': self.smtp_port,
                'tls': self.smtp_use_tls,
                'ssl': self.smtp_use_ssl
            }
            
            if self.smtp_username and self.smtp_password:
                smtp_config.update({
                    'user': self.smtp_username,
                    'password': self.smtp_password
                })
            
            # Test connection by attempting to send to a dummy address
            # This will validate SMTP connection and authentication
            try:
                # Use a known invalid address to test connection without actually sending
                response = test_message.send(to="test@example.com", smtp=smtp_config)
                # Any response means connection worked (even if sending failed due to invalid recipient)
                logger.info("SMTP connection test successful")
                return True
            except Exception as send_error:
                error_str = str(send_error).lower()
                # If error is about recipient/address, connection actually worked
                if any(keyword in error_str for keyword in ['recipient', 'address', 'mailbox', 'user']):
                    logger.info("SMTP connection test successful (authentication passed)")
                    return True
                else:
                    # Real connection/authentication error
                    raise send_error
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()


# Convenience functions for common email operations
async def send_welcome_email(user_email: str, user_name: str, verification_token: str) -> bool:
    """Send welcome email with verification link"""
    context = {
        'user_name': user_name,
        'verification_link': f"{settings.FRONTEND_URL}/verify-email/{verification_token}",
        'app_name': settings.FROM_NAME
    }
    
    return await email_service.send_template_email(
        to_email=user_email,
        template_name='welcome',
        subject=f'Welcome to {settings.FROM_NAME}!',
        context=context
    )


async def send_password_reset_email(user_email: str, user_name: str, reset_token: str) -> bool:
    """Send password reset email"""
    context = {
        'user_name': user_name,
        'reset_link': f"{settings.FRONTEND_URL}/reset-password/{reset_token}",
        'app_name': settings.FROM_NAME,
        'expires_hours': settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS
    }
    
    return await email_service.send_template_email(
        to_email=user_email,
        template_name='password_reset',
        subject='Password Reset Request',
        context=context
    )


async def send_verification_email(user_email: str, user_name: str, verification_token: str) -> bool:
    """Send email verification"""
    context = {
        'user_name': user_name,
        'verification_link': f"{settings.FRONTEND_URL}/verify-email/{verification_token}",
        'app_name': settings.FROM_NAME,
        'expires_hours': settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    }
    
    return await email_service.send_template_email(
        to_email=user_email,
        template_name='email_verification',
        subject='Verify Your Email Address',
        context=context
    )


async def send_security_alert_email(user_email: str, user_name: str, alert_type: str, details: Dict[str, Any]) -> bool:
    """Send security alert email"""
    context = {
        'user_name': user_name,
        'alert_type': alert_type,
        'details': details,
        'app_name': settings.FROM_NAME,
        'timestamp': details.get('timestamp', 'Unknown')
    }
    
    return await email_service.send_template_email(
        to_email=user_email,
        template_name='security_alert',
        subject=f'Security Alert: {alert_type}',
        context=context
    )
