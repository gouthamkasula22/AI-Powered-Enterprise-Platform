"""
Simple Template Service

Provides basic email template generation for authentication flows.
"""

from typing import Tuple


class SimpleTemplateService:
    """
    Simple template service for generating email content.
    Provides basic HTML and text templates for authentication emails.
    """
    
    def generate_verification_email(self, display_name: str, verification_token: str) -> Tuple[str, str]:
        """
        Generate email verification templates
        
        Returns:
            Tuple of (html_content, text_content)
        """
        verification_url = f"http://localhost:3000/verify-email?token={verification_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Welcome to Our Platform!</h2>
                <p>Hello {display_name},</p>
                <p>Thank you for signing up! Please verify your email address by clicking the link below:</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't sign up for an account, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Our Platform!
        
        Hello {display_name},
        
        Thank you for signing up! Please verify your email address by visiting this link:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't sign up for an account, you can safely ignore this email.
        """
        
        return html_content, text_content
    
    def generate_password_reset_email(self, display_name: str, reset_token: str) -> Tuple[str, str]:
        """
        Generate password reset email templates
        
        Returns:
            Tuple of (html_content, text_content)
        """
        reset_url = f"http://localhost:3000/reset-password/{reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF6B6B;">Password Reset Request</h2>
                <p>Hello {display_name},</p>
                <p>We received a request to reset your password. If you made this request, click the link below:</p>
                <p style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #FF6B6B; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't request a password reset, you can safely ignore this email. 
                    Your password will not be changed.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hello {display_name},
        
        We received a request to reset your password. If you made this request, visit this link:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
        """
        
        return html_content, text_content
    
    def generate_welcome_email(self, display_name: str) -> Tuple[str, str]:
        """
        Generate welcome email templates for newly verified users
        
        Returns:
            Tuple of (html_content, text_content)
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Our Platform!</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">🎉 Welcome aboard, {display_name}!</h2>
                <p>Hello {display_name},</p>
                <p>Congratulations! Your email has been successfully verified and your account is now active.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-top: 0;">What's next?</h3>
                    <ul style="color: #6c757d;">
                        <li>Complete your profile to personalize your experience</li>
                        <li>Explore our platform features</li>
                        <li>Secure your account with strong authentication</li>
                    </ul>
                </div>
                
                <p style="margin: 30px 0;">
                    <a href="http://localhost:3000/dashboard" 
                       style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Get Started
                    </a>
                </p>
                
                <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Thanks for joining us!<br>
                    The Platform Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        🎉 Welcome aboard, {display_name}!
        
        Hello {display_name},
        
        Congratulations! Your email has been successfully verified and your account is now active.
        
        What's next?
        - Complete your profile to personalize your experience
        - Explore our platform features  
        - Secure your account with strong authentication
        
        Get started by visiting: http://localhost:3000/dashboard
        
        If you have any questions or need assistance, feel free to reach out to our support team.
        
        Thanks for joining us!
        The Platform Team
        """
        
        return html_content, text_content