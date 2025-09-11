import importlib
import sys

# Force reload the modules to clear any cached state
if 'app.models.user' in sys.modules:
    del sys.modules['app.models.user']
if 'app.models' in sys.modules:
    del sys.modules['app.models']

# Import fresh
from app.models.user import User

print("User table columns after fresh import:")
for col in User.__table__.columns:
    print(f"  {col.name}: {col.type} (nullable: {col.nullable})")

print(f"\nTotal columns: {len(User.__table__.columns)}")

# Also check the class attributes
print("\nUser class attributes that are mapped columns:")
for attr_name in dir(User):
    attr = getattr(User, attr_name)
    if hasattr(attr, 'property') and hasattr(attr.property, 'columns'):
        print(f"  {attr_name}: {attr.property.columns[0].type}")
