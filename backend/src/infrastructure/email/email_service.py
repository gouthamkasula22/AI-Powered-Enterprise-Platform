"""
Email Service Infrastructure

Provides email sending capabilities using SMTP and SendGrid.
Supports both transactional emails and bulk sending.
"""

import smtplib
import ssl
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ...shared.config import get_settings


class EmailProvider(Enum):
    """Supported email providers"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"


@dataclass
class EmailMessage:
    """Email message data structure"""
    to: List[str]
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class IEmailService(ABC):
    """Email service interface"""
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> bool:
        """Send a single email"""
        pass
    
    @abstractmethod
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[bool]:
        """Send multiple emails"""
        pass


class SMTPEmailService(IEmailService):
    """
    SMTP-based email service.
    
    Uses standard SMTP protocol for sending emails.
    Good for development and small-scale production.
    """
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        default_from_email: Optional[str] = None,
        default_from_name: Optional[str] = None
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.default_from_email = default_from_email or username
        self.default_from_name = default_from_name or "Authentication System"
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send a single email via SMTP"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Attempting to send email to: {message.to}")
            logger.info(f"Subject: {message.subject}")
            logger.info(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
            logger.info(f"Username: {self.username}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name or self.default_from_name} <{message.from_email or self.default_from_email}>"
            msg['To'] = ', '.join(message.to)
            
            if message.cc:
                msg['Cc'] = ', '.join(message.cc)
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            
            # Add content
            if message.text_content:
                msg.attach(MIMEText(message.text_content, 'plain'))
            if message.html_content:
                msg.attach(MIMEText(message.html_content, 'html'))
            
            logger.info("Message prepared, attempting SMTP connection...")
            
            # Send email
            if self.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    logger.info("Connected to SMTP server")
                    server.starttls(context=context)
                    logger.info("TLS started")
                    server.login(self.username, self.password)
                    logger.info("SMTP login successful")
                    
                    recipients = message.to[:]
                    if message.cc:
                        recipients.extend(message.cc)
                    if message.bcc:
                        recipients.extend(message.bcc)
                    
                    logger.info(f"Sending to recipients: {recipients}")
                    server.send_message(msg, to_addrs=recipients)
                    logger.info("Email sent successfully via SMTP")
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    logger.info("Connected to SMTP server (no TLS)")
                    server.login(self.username, self.password)
                    logger.info("SMTP login successful")
                    
                    recipients = message.to[:]
                    if message.cc:
                        recipients.extend(message.cc)
                    if message.bcc:
                        recipients.extend(message.bcc)
                    
                    logger.info(f"Sending to recipients: {recipients}")
                    server.send_message(msg, to_addrs=recipients)
                    logger.info("Email sent successfully via SMTP")
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP email sending failed: {e}", exc_info=True)
            print(f"SMTP email sending failed: {e}")
            return False
    
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[bool]:
        """Send multiple emails via SMTP"""
        results = []
        for message in messages:
            result = await self.send_email(message)
            results.append(result)
        return results


class SendGridEmailService(IEmailService):
    """
    SendGrid-based email service.
    
    Uses SendGrid API for sending emails.
    Good for production with high volume and deliverability needs.
    """
    
    def __init__(
        self,
        api_key: str,
        default_from_email: str,
        default_from_name: str = "Authentication System"
    ):
        self.api_key = api_key
        self.default_from_email = default_from_email
        self.default_from_name = default_from_name
        
        # Store API key for later use
        self.api_key = api_key
        # SendGrid imports will be done when actually needed
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send a single email via SendGrid"""
        try:
            # Import SendGrid when actually needed
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail, From, To, Content
            except ImportError:
                print("SendGrid Python library is required. Install with: pip install sendgrid")
                return False
            
            # Initialize SendGrid client
            sg = SendGridAPIClient(api_key=self.api_key)
            
            # Build SendGrid message
            mail = Mail()
            
            # From
            mail.from_email = From(
                email=message.from_email or self.default_from_email,
                name=message.from_name or self.default_from_name
            )
            
            # To
            mail.to = [To(email=email) for email in message.to]
            
            # Subject
            mail.subject = message.subject
            
            # Content
            if message.text_content:
                mail.content = [Content("text/plain", message.text_content)]
            if message.html_content:
                if mail.content:
                    mail.content.append(Content("text/html", message.html_content))
                else:
                    mail.content = [Content("text/html", message.html_content)]
            
            # Optional fields
            if message.cc:
                mail.cc = [To(email=email) for email in message.cc]
            if message.bcc:
                mail.bcc = [To(email=email) for email in message.bcc]
            if message.reply_to:
                mail.reply_to = To(email=message.reply_to)
            
            # Send
            response = sg.send(mail)
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            print(f"SendGrid email sending failed: {e}")
            return False
    
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[bool]:
        """Send multiple emails via SendGrid"""
        results = []
        for message in messages:
            result = await self.send_email(message)
            results.append(result)
        return results


class EmailTemplateService:
    """
    Email template service for common authentication emails.
    
    Generates HTML and text content for verification, password reset, etc.
    """
    
    def __init__(self, base_url: str, app_name: str = "Authentication System"):
        self.base_url = base_url.rstrip('/')
        self.app_name = app_name
    
    def generate_verification_email(
        self, 
        user_name: str, 
        verification_token: str
    ) -> tuple[str, str]:
        """Generate email verification email content"""
        verification_url = f"{self.base_url}/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to {self.app_name}!</h2>
                <p>Hello {user_name},</p>
                <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{verification_url}</p>
                <p>This verification link will expire in 24 hours.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #7f8c8d;">
                    If you didn't create an account with {self.app_name}, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to {self.app_name}!
        
        Hello {user_name},
        
        Thank you for signing up! Please verify your email address by visiting this link:
        
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with {self.app_name}, please ignore this email.
        """
        
        return html_content, text_content
    
    def generate_password_reset_email(
        self, 
        user_name: str, 
        reset_token: str
    ) -> tuple[str, str]:
        """Generate password reset email content"""
        reset_url = f"{self.base_url}/reset-password/{reset_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Password Reset Request</h2>
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #e74c3c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
                <p>This reset link will expire in 1 hour.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #7f8c8d;">
                    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hello {user_name},
        
        We received a request to reset your password. Visit this link to create a new password:
        
        {reset_url}
        
        This reset link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        """
        
        return html_content, text_content
    
    def generate_welcome_email(
        self, 
        user_name: str
    ) -> tuple[str, str]:
        """Generate welcome email content for newly verified users"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #27ae60;">🎉 Welcome to {self.app_name}!</h2>
                <p>Hello {user_name},</p>
                <p>Congratulations! Your email has been successfully verified and your account is now fully active.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #27ae60;">
                    <h3 style="color: #2c3e50; margin-top: 0;">🚀 Ready to get started?</h3>
                    <ul style="color: #34495e; margin: 10px 0;">
                        <li>✅ Complete your profile information</li>
                        <li>🔒 Set up two-factor authentication for extra security</li>
                        <li>🎯 Explore all the features we have to offer</li>
                        <li>📱 Download our mobile app for on-the-go access</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.base_url}/dashboard" 
                       style="background-color: #27ae60; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Access Your Dashboard
                    </a>
                </div>
                
                <p>Need help getting started? Our support team is here to assist you every step of the way.</p>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2c3e50;">
                        <strong>💡 Pro Tip:</strong> Bookmark your dashboard for quick access: {self.base_url}/dashboard
                    </p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #7f8c8d;">
                    Welcome to the {self.app_name} community! We're excited to have you on board.<br>
                    <strong>The {self.app_name} Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        🎉 Welcome to {self.app_name}!
        
        Hello {user_name},
        
        Congratulations! Your email has been successfully verified and your account is now fully active.
        
        🚀 Ready to get started?
        ✅ Complete your profile information
        🔒 Set up two-factor authentication for extra security  
        🎯 Explore all the features we have to offer
        📱 Download our mobile app for on-the-go access
        
        Access your dashboard: {self.base_url}/dashboard
        
        Need help getting started? Our support team is here to assist you every step of the way.
        
        💡 Pro Tip: Bookmark your dashboard for quick access: {self.base_url}/dashboard
        
        Welcome to the {self.app_name} community! We're excited to have you on board.
        The {self.app_name} Team
        """
        
        return html_content, text_content


# Global email service instance
_email_service: Optional[IEmailService] = None
_template_service: Optional[EmailTemplateService] = None


def configure_email_service(
    provider: EmailProvider,
    **kwargs
) -> IEmailService:
    """Configure email service based on provider"""
    global _email_service
    
    if provider == EmailProvider.SMTP:
        _email_service = SMTPEmailService(**kwargs)
    elif provider == EmailProvider.SENDGRID:
        _email_service = SendGridEmailService(**kwargs)
    else:
        raise ValueError(f"Unsupported email provider: {provider}")
    
    return _email_service


def configure_email_templates(base_url: str, app_name: str) -> EmailTemplateService:
    """Configure email template service"""
    global _template_service
    _template_service = EmailTemplateService(base_url, app_name)
    return _template_service


def get_email_service() -> IEmailService:
    """Get configured email service"""
    if _email_service is None:
        raise RuntimeError("Email service not configured. Call configure_email_service() first.")
    return _email_service


def get_template_service() -> EmailTemplateService:
    """Get configured template service"""
    if _template_service is None:
        raise RuntimeError("Template service not configured. Call configure_email_templates() first.")
    return _template_service