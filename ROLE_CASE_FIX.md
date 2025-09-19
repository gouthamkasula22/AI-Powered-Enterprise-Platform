# Auth System Fix - Case Sensitivity in RBAC

## Problem Identified

After investigation, we found the following issues with the Role-Based Access Control (RBAC) system:

1. **Inconsistent Role Case**: The database had a mix of uppercase and lowercase role values:
   - Some users had `'admin'` while others had `'ADMIN'`
   - Some users had `'user'` while others had `'USER'`

2. **Model Definition Mismatch**: There are two UserModel classes in the codebase:
   - `src/infrastructure/database/models.py` - Has a `role` field (correct)
   - `src/infrastructure/database/models/user_model.py` - Missing the `role` field (outdated)

3. **Authentication Dependency Issue**: The `require_admin` function was not properly handling the case conversion.

## Fixes Applied

1. **Standardized Database Values**: Converted all role values in the database to uppercase for consistency.

2. **Documentation Update**: Added a comment to clarify that `_extract_role_value` already converts to lowercase.

3. **Model Import Fix**: Used the correct UserModel that has the role field.

## How the System Now Works

1. **Database Storage**: All roles are stored in UPPERCASE (`'ADMIN'`, `'USER'`, etc.)

2. **Role Conversion Process**:
   - When loading from database: `repositories.py` converts roles to lowercase (line 498)
   - This matches the UserRole enum values which are defined as lowercase (`user`, `admin`)

3. **Permission Checks**:
   - The `_extract_role_value` function converts any role to lowercase
   - The `require_admin` function compares against lowercase role values

## Recommendations for Future

1. **Add Schema Validation**: Enforce role case consistency at the database level.

2. **Merge Model Definitions**: Consolidate the multiple UserModel definitions.

3. **Add Tests**: Create specific tests for role-based access control with different case values.

4. **Configuration Option**: Consider adding a configuration option for case-sensitive role comparison.

## Test Results

The system now properly recognizes admin users in the database and should allow them access to the `/users` endpoint.

The following admin users were identified:
- test@example.com (ADMIN)
- admin@example.com (ADMIN)
- newtest@rbactest.com (ADMIN)
- newadmin@example.com (ADMIN)
- admin@rbactest.com (ADMIN)
- admin@roletest.com (ADMIN, previously 'admin')
- gk.qihydepark@gmail.com (ADMIN, previously 'admin')