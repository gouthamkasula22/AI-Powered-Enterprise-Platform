"""
Email Infrastructure

Email services for sending transactional emails, templates, and notifications.
"""

from .email_service import (
    EmailProvider,
    EmailMessage,
    IEmailService,
    SMTPEmailService,
    SendGridEmailService,
    EmailTemplateService,
    configure_email_service,
    configure_email_templates,
    get_email_service,
    get_template_service
)

__all__ = [
    "EmailProvider",
    "EmailMessage",
    "IEmailService",
    "SMTPEmailService",
    "SendGridEmailService", 
    "EmailTemplateService",
    "configure_email_service",
    "configure_email_templates",
    "get_email_service",
    "get_template_service"
]