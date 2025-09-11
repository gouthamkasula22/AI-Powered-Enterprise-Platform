"""
Email Validation Service

Comprehensive email validation including format checking, domain verification,
and disposable email detection for enhanced security.
"""

import re
import logging
from typing import Optional, List
from dataclasses import dataclass
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import dns.exception


logger = logging.getLogger(__name__)


@dataclass
class EmailValidationResult:
    """Result of email validation with detailed feedback"""
    is_valid: bool
    reason: Optional[str] = None
    suggestion: Optional[str] = None
    domain: Optional[str] = None
    normalized_email: Optional[str] = None


class EmailValidationService:
    """Service for comprehensive email validation"""
    
    # Common email domain typos and their corrections
    DOMAIN_SUGGESTIONS = {
        'gmial.com': 'gmail.com',
        'gmai.com': 'gmail.com',
        'gmail.co': 'gmail.com',
        'yahooo.com': 'yahoo.com',
        'yaho.com': 'yahoo.com',
        'hotmial.com': 'hotmail.com',
        'hotmai.com': 'hotmail.com',
        'outlok.com': 'outlook.com',
        'outlookc.com': 'outlook.com',
    }
    
    # Known disposable email domains (partial list)
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'temp-mail.org',
        'throwaway.email', 'dispostable.com', 'mailtemporary.com',
        'sharklasers.com', 'guerrillamail.info', 'guerrillamail.biz',
        'trashmail.com', 'spam4.me', 'maildrop.cc'
    }
    
    @staticmethod
    async def validate_email_comprehensive(email: str) -> EmailValidationResult:
        """
        Perform comprehensive email validation including:
        1. Format validation
        2. Domain existence check
        3. Disposable email detection
        4. Common typo suggestions
        
        Args:
            email: Email address to validate
            
        Returns:
            EmailValidationResult with validation details
        """
        try:
            # Phase 1: Basic format validation and normalization
            logger.debug(f"Validating email: {email}")
            
            # Check for obvious format issues first
            if not email or '@' not in email:
                return EmailValidationResult(
                    is_valid=False,
                    reason="Email format is invalid"
                )
            
            # Use email-validator for comprehensive format checking
            try:
                validated_email = validate_email(
                    email,
                    check_deliverability=False  # We'll do our own domain check
                )
                normalized_email = validated_email.email
                domain = validated_email.domain.lower()
                
            except EmailNotValidError as e:
                # Check if this might be a common typo
                suggestion = EmailValidationService._get_domain_suggestion(email)
                return EmailValidationResult(
                    is_valid=False,
                    reason=f"Email format is invalid: {str(e)}",
                    suggestion=suggestion
                )
            
            # Phase 2: Domain existence check
            logger.debug(f"Checking domain existence: {domain}")
            domain_exists = await EmailValidationService._check_domain_exists(domain)
            if not domain_exists:
                suggestion = EmailValidationService._get_domain_suggestion(email)
                return EmailValidationResult(
                    is_valid=False,
                    reason="Domain does not exist",
                    suggestion=suggestion,
                    domain=domain
                )
            
            # Phase 3: Check for disposable email
            logger.debug(f"Checking for disposable domain: {domain}")
            if EmailValidationService._is_disposable_email(domain):
                return EmailValidationResult(
                    is_valid=False,
                    reason="Disposable email addresses are not allowed",
                    domain=domain
                )
            
            # Phase 4: Check for deliverability (MX record)
            logger.debug(f"Checking MX records for: {domain}")
            has_mx = await EmailValidationService._check_mx_record(domain)
            if not has_mx:
                return EmailValidationResult(
                    is_valid=False,
                    reason="Email cannot receive messages (no MX record)",
                    domain=domain
                )
            
            logger.info(f"Email validation successful: {normalized_email}")
            return EmailValidationResult(
                is_valid=True,
                normalized_email=normalized_email,
                domain=domain
            )
            
        except Exception as e:
            logger.error(f"Email validation error: {str(e)}")
            return EmailValidationResult(
                is_valid=False,
                reason="Email validation failed due to technical error"
            )
    
    @staticmethod
    async def _check_domain_exists(domain: str) -> bool:
        """Check if domain exists via DNS lookup"""
        try:
            # Try to resolve the domain
            dns.resolver.resolve(domain, 'A')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            try:
                # Also try AAAA record (IPv6)
                dns.resolver.resolve(domain, 'AAAA')
                return True
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
                return False
        except Exception as e:
            logger.warning(f"DNS lookup error for {domain}: {str(e)}")
            # If DNS lookup fails due to network issues, assume domain exists
            # to avoid false negatives
            return True
    
    @staticmethod
    async def _check_mx_record(domain: str) -> bool:
        """Check if domain has MX record (can receive email)"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            return False
        except Exception as e:
            logger.warning(f"MX record lookup error for {domain}: {str(e)}")
            # If MX lookup fails, assume it can receive email
            return True
    
    @staticmethod
    def _is_disposable_email(domain: str) -> bool:
        """Check if domain is a known disposable email service"""
        return domain.lower() in EmailValidationService.DISPOSABLE_DOMAINS
    
    @staticmethod
    def _get_domain_suggestion(email: str) -> Optional[str]:
        """Get domain suggestion for common typos"""
        try:
            if '@' not in email:
                return None
                
            local_part, domain = email.rsplit('@', 1)
            domain = domain.lower()
            
            if domain in EmailValidationService.DOMAIN_SUGGESTIONS:
                suggested_domain = EmailValidationService.DOMAIN_SUGGESTIONS[domain]
                return f"{local_part}@{suggested_domain}"
                
            return None
        except Exception:
            return None
    
    @staticmethod
    async def validate_email_basic(email: str) -> bool:
        """Simple boolean validation for quick checks"""
        result = await EmailValidationService.validate_email_comprehensive(email)
        return result.is_valid
