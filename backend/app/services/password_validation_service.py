"""
Password Validation Service

Comprehensive password validation with strength checking and detailed feedback
for enhanced security and user experience.
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PasswordRequirement:
    """Individual password requirement with check result"""
    name: str
    description: str
    is_met: bool
    pattern: Optional[str] = None


@dataclass
class PasswordValidationResult:
    """Complete password validation result with detailed feedback"""
    is_valid: bool
    strength_score: int  # 0-100
    strength_level: str  # "Weak", "Fair", "Good", "Strong", "Very Strong"
    requirements: List[PasswordRequirement]
    suggestions: List[str]
    estimated_crack_time: str


class PasswordValidationService:
    """Service for comprehensive password validation and strength assessment"""
    
    # Password requirements configuration
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    # Common weak passwords (partial list)
    COMMON_PASSWORDS = {
        'password', 'password123', '123456', '123456789', 'qwerty',
        'abc123', 'password1', 'admin', 'letmein', 'welcome',
        'monkey', '1234567890', 'iloveyou', '123123', 'password!',
        'test123', 'user123', '000000', 'root', 'toor'
    }
    
    # Common password patterns to avoid
    WEAK_PATTERNS = [
        r'^(.)\1{7,}$',  # Same character repeated
        r'^(012|123|234|345|456|567|678|789|890|901)+',  # Sequential numbers
        r'^(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)+',  # Sequential letters
        r'^(qwe|wer|ert|rty|tyu|yui|uio|iop|asd|sdf|dfg|fgh|ghj|hjk|jkl|zxc|xcv|cvb|vbn|bnm)+',  # Keyboard patterns
    ]

    def validate_password(self, password: str, email: Optional[str] = None) -> PasswordValidationResult:
        """
        Comprehensive password validation with detailed feedback
        
        Args:
            password: Password to validate
            email: User's email for personalized checking (optional)
            
        Returns:
            PasswordValidationResult with detailed validation results
        """
        try:
            requirements = self._check_requirements(password, email)
            strength_score = self._calculate_strength_score(password, requirements)
            strength_level = self._get_strength_level(strength_score)
            suggestions = self._generate_suggestions(requirements, password)
            crack_time = self._estimate_crack_time(strength_score)
            
            is_valid = all(req.is_met for req in requirements)
            
            return PasswordValidationResult(
                is_valid=is_valid,
                strength_score=strength_score,
                strength_level=strength_level,
                requirements=requirements,
                suggestions=suggestions,
                estimated_crack_time=crack_time
            )
            
        except Exception as e:
            logger.error(f"Password validation error: {str(e)}")
            # Return safe default for errors
            return PasswordValidationResult(
                is_valid=False,
                strength_score=0,
                strength_level="Error",
                requirements=[],
                suggestions=["Password validation error occurred"],
                estimated_crack_time="Unknown"
            )

    def _check_requirements(self, password: str, email: Optional[str] = None) -> List[PasswordRequirement]:
        """Check all password requirements"""
        requirements = []
        
        # Length requirement
        requirements.append(PasswordRequirement(
            name="length",
            description=f"At least {self.MIN_LENGTH} characters long",
            is_met=len(password) >= self.MIN_LENGTH
        ))
        
        # Maximum length
        requirements.append(PasswordRequirement(
            name="max_length",
            description=f"No more than {self.MAX_LENGTH} characters",
            is_met=len(password) <= self.MAX_LENGTH
        ))
        
        # Lowercase letter
        requirements.append(PasswordRequirement(
            name="lowercase",
            description="Contains at least one lowercase letter (a-z)",
            is_met=bool(re.search(r'[a-z]', password)),
            pattern=r'[a-z]'
        ))
        
        # Uppercase letter
        requirements.append(PasswordRequirement(
            name="uppercase",
            description="Contains at least one uppercase letter (A-Z)",
            is_met=bool(re.search(r'[A-Z]', password)),
            pattern=r'[A-Z]'
        ))
        
        # Number
        requirements.append(PasswordRequirement(
            name="number",
            description="Contains at least one number (0-9)",
            is_met=bool(re.search(r'\d', password)),
            pattern=r'\d'
        ))
        
        # Special character
        requirements.append(PasswordRequirement(
            name="special",
            description="Contains at least one special character (!@#$%^&*)",
            is_met=bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password)),
            pattern=r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]'
        ))
        
        # No common passwords
        requirements.append(PasswordRequirement(
            name="not_common",
            description="Not a commonly used password",
            is_met=password.lower() not in self.COMMON_PASSWORDS
        ))
        
        # No weak patterns
        has_weak_pattern = any(re.search(pattern, password.lower()) for pattern in self.WEAK_PATTERNS)
        requirements.append(PasswordRequirement(
            name="no_weak_patterns",
            description="Avoids predictable patterns (123, abc, qwerty, etc.)",
            is_met=not has_weak_pattern
        ))
        
        # No email in password (if email provided)
        if email:
            email_parts = email.lower().split('@')[0].split('.')
            has_email_part = any(part in password.lower() for part in email_parts if len(part) > 2)
            requirements.append(PasswordRequirement(
                name="no_email",
                description="Does not contain parts of your email address",
                is_met=not has_email_part
            ))
        
        return requirements

    def _calculate_strength_score(self, password: str, requirements: List[PasswordRequirement]) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Base score from requirements
        met_requirements = sum(1 for req in requirements if req.is_met)
        score += (met_requirements / len(requirements)) * 60
        
        # Length bonus
        if len(password) >= 12:
            score += 15
        elif len(password) >= 10:
            score += 10
        elif len(password) >= 8:
            score += 5
        
        # Character variety bonus
        char_types = 0
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'\d', password):
            char_types += 1
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
            char_types += 1
        
        score += (char_types / 4) * 15
        
        # Unique character bonus
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.8:
            score += 10
        elif unique_chars >= len(password) * 0.6:
            score += 5
        
        return min(100, max(0, int(score)))

    def _get_strength_level(self, score: int) -> str:
        """Convert score to strength level"""
        if score >= 90:
            return "Very Strong"
        elif score >= 75:
            return "Strong"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Weak"

    def _generate_suggestions(self, requirements: List[PasswordRequirement], password: str) -> List[str]:
        """Generate helpful suggestions for improving password"""
        suggestions = []
        
        unmet_requirements = [req for req in requirements if not req.is_met]
        
        if not unmet_requirements:
            if len(password) < 12:
                suggestions.append("Consider using 12+ characters for extra security")
            return suggestions
        
        # Priority suggestions
        for req in unmet_requirements:
            if req.name == "length":
                suggestions.append(f"Make your password at least {self.MIN_LENGTH} characters long")
            elif req.name == "lowercase":
                suggestions.append("Add some lowercase letters (a-z)")
            elif req.name == "uppercase":
                suggestions.append("Add some uppercase letters (A-Z)")
            elif req.name == "number":
                suggestions.append("Include at least one number (0-9)")
            elif req.name == "special":
                suggestions.append("Add a special character like !@#$%^&*")
            elif req.name == "not_common":
                suggestions.append("Avoid common passwords - be more creative")
            elif req.name == "no_weak_patterns":
                suggestions.append("Avoid predictable patterns like 123, abc, or qwerty")
            elif req.name == "no_email":
                suggestions.append("Don't include parts of your email in your password")
        
        return suggestions

    def _estimate_crack_time(self, score: int) -> str:
        """Estimate time to crack password based on strength"""
        if score >= 90:
            return "Centuries"
        elif score >= 80:
            return "Decades"
        elif score >= 70:
            return "Years"
        elif score >= 60:
            return "Months"
        elif score >= 50:
            return "Weeks"
        elif score >= 40:
            return "Days"
        elif score >= 30:
            return "Hours"
        else:
            return "Minutes"

    def get_password_requirements_info(self) -> Dict[str, str]:
        """Get password requirements for display to users"""
        return {
            "length": f"At least {self.MIN_LENGTH} characters long",
            "lowercase": "Contains at least one lowercase letter (a-z)",
            "uppercase": "Contains at least one uppercase letter (A-Z)",
            "number": "Contains at least one number (0-9)",
            "special": "Contains at least one special character (!@#$%^&*)",
            "not_common": "Not a commonly used password",
            "no_patterns": "Avoids predictable patterns (123, abc, qwerty)",
            "no_personal": "Does not contain personal information"
        }
