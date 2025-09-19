"""Debug script to inspect a user's stored role and status.

Usage (PowerShell):
  cd backend
  python scripts/debug_user_role.py --email you@example.com
"""

import asyncio
import argparse
from sqlalchemy import text
import os
import sys

# Ensure project root on path so settings & models import works
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

from src.infrastructure.database.database import get_database_manager


async def main():
	parser = argparse.ArgumentParser(description="Inspect user role")
	parser.add_argument("--email", required=True, help="User email to inspect")
	args = parser.parse_args()

	db_manager = get_database_manager()
	if not db_manager.is_initialized:
		await db_manager.initialize()

	async for session in db_manager.get_session():
		result = await session.execute(text("SELECT id, email, role, is_active, is_verified, is_staff, is_superuser FROM users WHERE email = :email"), {"email": args.email})
		row = result.first()
		if not row:
			print(f"❌ No user found with email {args.email}")
			return
		print("User Record:")
		print(f"  ID:           {row.id}")
		print(f"  Email:        {row.email}")
		print(f"  Role (raw):   {row.role}")
		print(f"  is_active:    {row.is_active}")
		print(f"  is_verified:  {row.is_verified}")
		print(f"  is_staff:     {row.is_staff}")
		print(f"  is_superuser: {row.is_superuser}")
		normalized = str(row.role).lower() if row.role else ''
		print(f"  Normalized:   {normalized}")
		is_admin = normalized in ("admin", "superadmin")
		print(f"  is_admin?:    {is_admin}")


if __name__ == "__main__":
	asyncio.run(main())
