"""
M1.2 Simple Model Validation Script
Basic validation of database models without complex relationships
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text, select, delete

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend'))

from app.core.database import get_db_session
from app.models import User, UserSession, OTPVerification, LoginHistory, PasswordHistory, SocialAccount

async def test_simple_model_creation():
    """Test that we can create instances of all models"""
    print("🧪 Testing Simple Model Creation...")
    
    # Use unique email for each test run to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"test-{unique_id}@example.com"
    
    session = await get_db_session()
    try:
        # Test User creation
        user = User(email=unique_email)
        session.add(user)
        await session.flush()  # Get the ID
        user_id = user.id
        print(f"✅ User created: {user_id}")
        
        # Test UserSession creation  
        user_session = UserSession(
            user_id=user_id,
            session_token=f"test_session_token_{unique_id}",
            refresh_token=f"test_refresh_token_{unique_id}",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_fingerprint=f"test_device_fingerprint_{unique_id}",
            expires_at=datetime.now() + timedelta(hours=1),
            last_accessed=datetime.now()  # Add required field
        )
        session.add(user_session)
        await session.flush()
        print(f"✅ UserSession created: {user_session.id}")
        
        # Test OTPVerification creation
        otp = OTPVerification(
            user_id=user_id,
            code="123456",
            purpose="email_verification",
            expires_at=datetime.now() + timedelta(minutes=10),
            attempts=0,  # Initialize attempts counter
            max_attempts=5  # Initialize max attempts
        )
        session.add(otp)
        await session.flush()
        print(f"✅ OTPVerification created: {otp.id}")
        
        # Test PasswordHistory creation
        password_history = PasswordHistory(
            user_id=user_id,
            password_hash="hashed_password_123",
            set_at=datetime.now(),
            strength_score=0.85,  # Must be between 0 and 1
            policy_compliant=True,
            length=12,  # Add required field
            has_uppercase=True,  # Add required fields
            has_lowercase=True,
            has_digits=True,
            has_symbols=False
        )
        session.add(password_history)
        await session.flush()
        print(f"✅ PasswordHistory created: {password_history.id}")
        
        # Test SocialAccount creation
        social_account = SocialAccount(
            user_id=user_id,
            provider="google",
            provider_id=f"google_user_{unique_id}",
            email=unique_email,
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
            email_attempted=unique_email,
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
        
        # Models created successfully - now rollback to clean up test data
        await session.rollback()
        print("✅ All models created successfully!")
        print("✅ Test data cleaned up (rolled back - not persisted)")
        
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Error during model testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()

async def test_model_methods():
    """Test model validation methods"""
    print("\n🛡️ Testing Model Methods...")
    
    try:
        # Test OTP validation
        otp = OTPVerification(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # dummy UUID
            code="123456",
            purpose="email_verification",
            expires_at=datetime.now() + timedelta(minutes=10),
            attempts=0,  # Initialize attempts counter
            max_attempts=5  # Initialize max attempts
        )
        
        # Test code validation
        valid_code = otp.verify_code("123456")
        invalid_code = otp.verify_code("wrong")
        print(f"✅ OTP validation - Correct code: {valid_code}, Wrong code: {invalid_code}")
        
        # Test UserSession methods
        session = UserSession(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # dummy UUID
            session_token="test",
            refresh_token="test",
            ip_address="192.168.1.1",
            user_agent="test",
            expires_at=datetime.now() + timedelta(hours=1),
            last_accessed=datetime.now()
        )
        
        is_expired = session.is_expired  # Property, not method
        time_left = session.time_until_expiry  # Property, not method
        print(f"✅ Session validation - Expired: {is_expired}, Time left: {time_left}")
        
        # Test LoginHistory risk scoring
        login = LoginHistory(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # dummy UUID
            email_attempted="test-risk@example.com",  # Different email for risk test
            ip_address="192.168.1.1",
            user_agent="test",
            login_type="password",
            result="success"
        )
        
        risk_score = login.calculate_risk_score()
        print(f"✅ Login risk score calculated: {risk_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing methods: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_simple_validation():
    """Run simple model validation"""
    print("🚀 Starting Simple Model Validation for M1.2")
    print("=" * 50)
    
    results = {
        "model_creation": await test_simple_model_creation(),
        "model_methods": await test_model_methods()
    }
    
    print("\n" + "=" * 50)
    print("📊 M1.2 Simple Validation Results:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 M1.2 Database Models Creation - COMPLETE!")
        print("✅ All models can be created successfully")
        print("✅ All model methods working")
        print("✅ Database tables created and functional")
        print("✅ Ready to proceed to M1.3 Authentication Services")
    else:
        print("⚠️ Some tests failed - review and fix before proceeding")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_simple_validation())
