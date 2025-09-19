"""
Fix script for the UserModel to Role mismatch issue.

This script:
1. Analyzes the database schema vs model definition
2. Checks how roles are compared in the auth system
3. Provides a fix to make the authorization system work properly
"""

import sys
import os
import asyncio
import argparse
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_auth")

# Database connection info
DB_URL = "postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db"

async def analyze_auth_system():
    """Analyze the authentication and authorization system"""
    try:
        # Connect to database
        engine = create_async_engine(DB_URL, echo=False)
        async_session_factory = async_sessionmaker(
            bind=engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async with async_session_factory() as session:
            # 1. Check user roles in database
            sql = text("""
                SELECT email, role, is_staff, is_superuser
                FROM users
                WHERE role IS NOT NULL
                ORDER BY role
            """)
            result = await session.execute(sql)
            users_with_roles = result.fetchall()
            
            logger.info(f"Found {len(users_with_roles)} users with roles:")
            for user in users_with_roles:
                logger.info(f"  - {user.email}: role='{user.role}', is_staff={user.is_staff}, is_superuser={user.is_superuser}")
            
            # 2. Check for case consistency in roles
            role_cases = {}
            for user in users_with_roles:
                if user.role.lower() not in role_cases:
                    role_cases[user.role.lower()] = set()
                role_cases[user.role.lower()].add(user.role)
            
            logger.info("\nRole case variations:")
            for role_lower, variations in role_cases.items():
                logger.info(f"  - {role_lower}: {variations}")
            
            # 3. Identify if we need standardization
            needs_standardization = any(len(variations) > 1 for variations in role_cases.values())
            if needs_standardization:
                logger.warning("⚠️ Role case inconsistency detected! This could cause authorization issues.")
            else:
                logger.info("✅ Role cases are consistent.")
            
            # 4. Check token records if they exist
            try:
                sql = text("""
                    SELECT COUNT(*) as count
                    FROM token_blacklist
                """)
                result = await session.execute(sql)
                count = result.fetchone()
                logger.info(f"\nToken blacklist entries: {count.count if count else 0}")
            except Exception:
                logger.info("\nToken blacklist table not found or not accessible")
            
            return {
                "users_with_roles": users_with_roles,
                "role_cases": role_cases,
                "needs_standardization": needs_standardization
            }
            
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return None

async def standardize_roles(case='upper'):
    """Standardize role values to all uppercase or lowercase"""
    if case not in ('upper', 'lower'):
        logger.error("Case must be 'upper' or 'lower'")
        return False
    
    try:
        # Connect to database
        engine = create_async_engine(DB_URL, echo=False)
        async_session_factory = async_sessionmaker(
            bind=engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async with async_session_factory() as session:
            # Get current roles before update
            sql = text("SELECT id, email, role FROM users WHERE role IS NOT NULL")
            result = await session.execute(sql)
            users_before = {row.id: row.role for row in result.fetchall()}
            
            # Update all roles to standardized case
            if case == 'upper':
                sql = text("UPDATE users SET role = UPPER(role) WHERE role IS NOT NULL")
            else:
                sql = text("UPDATE users SET role = LOWER(role) WHERE role IS NOT NULL")
                
            await session.execute(sql)
            await session.commit()
            
            # Get roles after update
            sql = text("SELECT id, email, role FROM users WHERE role IS NOT NULL")
            result = await session.execute(sql)
            users_after = {row.id: row.role for row in result.fetchall()}
            
            # Show changes
            logger.info(f"Standardized roles to {case.upper()}CASE:")
            changes = 0
            for user_id, role_before in users_before.items():
                role_after = users_after.get(user_id)
                if role_before != role_after:
                    changes += 1
                    logger.info(f"  - User {user_id}: {role_before} → {role_after}")
            
            logger.info(f"✅ Updated {changes} user roles")
            return True
            
    except Exception as e:
        logger.error(f"Standardization failed: {str(e)}", exc_info=True)
        return False

async def main():
    parser = argparse.ArgumentParser(description="Analyze and fix authentication issues")
    parser.add_argument("--analyze", action="store_true", help="Analyze the auth system")
    parser.add_argument("--fix", action="store_true", help="Fix role case inconsistencies")
    parser.add_argument("--case", choices=["upper", "lower"], default="upper", 
                        help="Case to standardize roles (upper or lower)")
    args = parser.parse_args()
    
    if not (args.analyze or args.fix):
        parser.print_help()
        return
    
    if args.analyze:
        await analyze_auth_system()
    
    if args.fix:
        logger.info(f"Standardizing roles to {args.case.upper()}CASE...")
        success = await standardize_roles(args.case)
        if success:
            logger.info("\nRecommended next steps:")
            logger.info("1. Make sure your UserRole comparison in auth.py is case-insensitive")
            logger.info("2. Consider adding a check in require_admin function like:")
            logger.info("   user_role = user_role.upper()  # Standardize for comparison")
            logger.info("   if user_role in ('ADMIN', 'SUPERADMIN'):")
            logger.info("3. Test /users endpoint with admin user login")

if __name__ == "__main__":
    asyncio.run(main())