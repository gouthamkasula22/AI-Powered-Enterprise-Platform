"""Utility script to update a user's role.

Usage (PowerShell):
  cd backend
  python scripts/fix_user_role.py --email you@example.com --role ADMIN

Roles accepted: USER, ADMIN, SUPERADMIN (case-insensitive)
"""

import asyncio
import argparse
from sqlalchemy import text
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

from src.infrastructure.database.database import get_database_manager

VALID_ROLES = {"user", "admin", "superadmin"}


async def main():
	parser = argparse.ArgumentParser(description="Update user role")
	parser.add_argument("--email", required=True, help="User email")
	parser.add_argument("--role", required=True, help="New role (USER|ADMIN|SUPERADMIN)")
	args = parser.parse_args()

	new_role = args.role.strip().lower()
	if new_role not in VALID_ROLES:
		print(f"❌ Invalid role '{args.role}'. Valid: {', '.join(r.upper() for r in VALID_ROLES)}")
		return

	db_manager = get_database_manager()
	if not db_manager.is_initialized:
		await db_manager.initialize()

	async for session in db_manager.get_session():
		# Check current
		result = await session.execute(text("SELECT id, role FROM users WHERE email = :email"), {"email": args.email})
		row = result.first()
		if not row:
			print(f"❌ No user found with email {args.email}")
			return
		print(f"Current role for {args.email}: {row.role}")
		if row.role and row.role.lower() == new_role:
			print("✅ Role already set. No change needed.")
			return
		await session.execute(text("UPDATE users SET role = :role WHERE id = :id"), {"role": new_role.upper(), "id": row.id})
		print(f"🔄 Updated role to {new_role.upper()} (id={row.id})")
		# Re-fetch
		result2 = await session.execute(text("SELECT role FROM users WHERE id = :id"), {"id": row.id})
		new_row = result2.first()
		print(f"✅ New stored role: {new_row.role if new_row else 'UNKNOWN'}")


if __name__ == "__main__":
	asyncio.run(main())
