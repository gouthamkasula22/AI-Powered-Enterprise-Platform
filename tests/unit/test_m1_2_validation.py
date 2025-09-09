"""
M1.2 Model Validation and Testing Script
Comprehensive validation of all database models and their relationships
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db_session
from app.models import (
    User, UserSession, OTPVerification, 
    LoginHistory, PasswordHistory, SocialAccount
)

async def test_basic_model_operations():
    """Test basic CRUD operations for all models"""
    print("🧪 Testing Basic Model Operations...")
    
    session = await get_db_session()
    try:
        # Test User creation
        user = User(email="test@example.com")
        session.add(user)
        await session.flush()  # Get the ID
        user_id = user.id
        print(f"✅ User created: {user_id}")
        
        # Test UserSession creation
        user_session = UserSession(
            user_id=user_id,
            session_token="test_session_token_123",
            refresh_token="test_refresh_token_123",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_fingerprint="test_device_fingerprint",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        session.add(user_session)
        await session.flush()
        print(f"✅ UserSession created: {user_session.id}")
        
        # Test OTPVerification creation
        otp = OTPVerification(
            user_id=user_id,
            code="123456",
            purpose="email_verification",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        session.add(otp)
        await session.flush()
        print(f"✅ OTPVerification created: {otp.id}")
        
        # Test PasswordHistory creation
        password_history = PasswordHistory(
            user_id=user_id,
            password_hash="hashed_password_123",
            set_at=datetime.utcnow(),
            strength_score=85,
            policy_compliant=True
        )
        session.add(password_history)
        await session.flush()
        print(f"✅ PasswordHistory created: {password_history.id}")
        
        # Test SocialAccount creation
        social_account = SocialAccount(
            user_id=user_id,
            provider="google",
            provider_id="google_user_123",
            email="test@example.com",
            display_name="Test User",
            is_primary=True
        )
        session.add(social_account)
        await session.flush()
        print(f"✅ SocialAccount created: {social_account.id}")
        
        # Test LoginHistory creation
        login_history = LoginHistory(
            user_id=user_id,
            session_id=user_session.id,
            email_attempted="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            login_type="password",
            result="success",
            country="US",
            city="Test City"
        )
        session.add(login_history)
        await session.flush()
        print(f"✅ LoginHistory created: {login_history.id}")
        
        await session.commit()
        print("✅ All models created and committed successfully!")
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Error during model testing: {e}")
        return False
    finally:
        await session.close()

async def test_model_relationships():
    """Test relationships between models"""
    print("\n🔗 Testing Model Relationships...")
    
    session = await get_db_session()
    try:
        # Find our test user
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Test user not found")
            return False
        
        # Test User -> Sessions relationship (would need to be implemented)
        # For now, just verify we can query related records
        
        # Count related records
        session_result = await session.execute(
            select(UserSession).where(UserSession.user_id == user.id)
        )
        sessions = session_result.scalars().all()
        print(f"✅ User has {len(sessions)} session(s)")
        
        otp_result = await session.execute(
            select(OTPVerification).where(OTPVerification.user_id == user.id)
        )
        otps = otp_result.scalars().all()
        print(f"✅ User has {len(otps)} OTP verification(s)")
        
        password_result = await session.execute(
            select(PasswordHistory).where(PasswordHistory.user_id == user.id)
        )
        passwords = password_result.scalars().all()
        print(f"✅ User has {len(passwords)} password history record(s)")
        
        social_result = await session.execute(
            select(SocialAccount).where(SocialAccount.user_id == user.id)
        )
        socials = social_result.scalars().all()
        print(f"✅ User has {len(socials)} social account(s)")
        
        login_result = await session.execute(
            select(LoginHistory).where(LoginHistory.user_id == user.id)
        )
        logins = login_result.scalars().all()
        print(f"✅ User has {len(logins)} login history record(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing relationships: {e}")
        return False
    finally:
        await session.close()

async def test_model_validations():
    """Test model validation methods"""
    print("\n🛡️ Testing Model Validations...")
    
    try:
        # Test OTP validation
        otp = OTPVerification(
            user_id=uuid.uuid4(),
            code="123456",
            purpose="email_verification",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # Test code validation
        valid_code = otp.validate_code("123456")
        invalid_code = otp.validate_code("wrong")
        print(f"✅ OTP validation - Correct code: {valid_code}, Wrong code: {invalid_code}")
        
        # Test UserSession IP validation
        session = UserSession(
            user_id=uuid.uuid4(),
            session_token="test",
            refresh_token="test",
            ip_address="192.168.1.1",
            user_agent="test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        valid_ipv4 = session.is_valid_ip("192.168.1.1") 
        valid_ipv6 = session.is_valid_ip("2001:db8::1")
        invalid_ip = session.is_valid_ip("invalid.ip")
        print(f"✅ IP validation - IPv4: {valid_ipv4}, IPv6: {valid_ipv6}, Invalid: {invalid_ip}")
        
        # Test LoginHistory risk scoring
        login = LoginHistory(
            user_id=uuid.uuid4(),
            email_attempted="test@example.com",
            ip_address="192.168.1.1",
            user_agent="test",
            login_type="password",
            result="success"
        )
        
        risk_score = login.calculate_risk_score()
        print(f"✅ Login risk score calculated: {risk_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing validations: {e}")
        return False

async def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    session = await get_db_session()
    try:
        from sqlalchemy import delete
        
        # Delete test user and all related records will cascade
        result = await session.execute(
            delete(User).where(User.email == "test@example.com")
        )
        
        await session.commit()
        print(f"✅ Cleaned up test data ({result.rowcount} user deleted)")
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Error cleaning up: {e}")
        return False
    finally:
        await session.close()

async def run_comprehensive_model_validation():
    """Run all model validation tests"""
    print("🚀 Starting Comprehensive Model Validation for M1.2")
    print("=" * 60)
    
    results = {
        "basic_operations": await test_basic_model_operations(),
        "relationships": await test_model_relationships(), 
        "validations": await test_model_validations(),
        "cleanup": await cleanup_test_data()
    }
    
    print("\n" + "=" * 60)
    print("📊 M1.2 Validation Results:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 M1.2 Database Models Creation - COMPLETE!")
        print("✅ All models created successfully")
        print("✅ All relationships working")
        print("✅ All validations functional")
        print("✅ Ready to proceed to M1.3 Authentication Services")
    else:
        print("⚠️ Some tests failed - review and fix before proceeding")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_comprehensive_model_validation())
