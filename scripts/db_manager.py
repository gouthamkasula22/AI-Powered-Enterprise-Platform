#!/usr/bin/env python3
"""
Database User Management Script
Quick commands to manage users in the database
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def show_users():
    """List all registered users"""
    print("🔍 Fetching users from database...")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.id, User.email, User.first_name, User.last_name, User.created_at, User.is_verified)
            .order_by(User.created_at.desc())
        )
        users = result.all()
        
        print(f"\n📋 Found {len(users)} users:")
        print("-" * 80)
        
        if users:
            for user in users:
                status = "✅ Verified" if user.is_verified else "⏳ Pending"
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print(f"Name: {user.first_name} {user.last_name}")
                print(f"Status: {status}")
                print(f"Created: {user.created_at}")
                print("-" * 80)
        else:
            print("No users found in database.")

async def delete_user_by_email(email: str):
    """Delete a specific user by email"""
    print(f"🗑️  Deleting user: {email}")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(User).where(User.email == email)
        )
        await session.commit()
        
        if result.rowcount > 0:
            print(f"✅ Successfully deleted user: {email}")
        else:
            print(f"❌ User not found: {email}")

async def delete_all_users():
    """Delete all users (with confirmation)"""
    async with AsyncSessionLocal() as session:
        # First, show count
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        
        if count == 0:
            print("📭 No users found in database.")
            return
        
        print(f"⚠️  WARNING: This will delete ALL {count} users from the database!")
        confirm = input("Type 'DELETE ALL' to confirm (case-sensitive): ")
        
        if confirm == "DELETE ALL":
            result = await session.execute(delete(User))
            await session.commit()
            print(f"✅ Successfully deleted {result.rowcount} users")
            print("🔄 Database is now empty")
        else:
            print("❌ Deletion cancelled - no users were deleted")

async def count_users():
    """Count total users"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        print(f"👥 Total users in database: {count}")

def print_menu():
    """Print the main menu"""
    print("\n" + "=" * 50)
    print("🗄️  DATABASE USER MANAGEMENT")
    print("=" * 50)
    print("1. 📋 List all users")
    print("2. 👥 Count users") 
    print("3. 🗑️  Delete user by email")
    print("4. 💥 Delete ALL users")
    print("5. 🚪 Exit")
    print("-" * 50)

async def main():
    """Main interactive menu"""
    while True:
        print_menu()
        choice = input("Choose an option (1-5): ").strip()
        
        try:
            if choice == "1":
                await show_users()
                
            elif choice == "2":
                await count_users()
                
            elif choice == "3":
                email = input("Enter email address to delete: ").strip()
                if email:
                    await delete_user_by_email(email)
                else:
                    print("❌ No email provided")
                    
            elif choice == "4":
                await delete_all_users()
                
            elif choice == "5":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("🚀 Starting Database User Management Tool...")
    asyncio.run(main())
