# Git Best Practices for File Operations

## Moving Files

❌ **Don't use PowerShell Move-Item:**
```powershell
Move-Item "source\file.py" "destination\file.py"
```

✅ **Use git mv instead:**
```bash
git mv source/file.py destination/file.py
```

## Why git mv is better:

1. **Preserves Git History**: Git tracks the file as moved, not deleted and recreated
2. **Better Diffs**: Git can show what changed in the file vs just showing deleted/added
3. **Blame/History**: `git blame` and `git log` work properly across the move
4. **Cleaner Status**: Git status shows "renamed" instead of "deleted/added"

## Renaming Files

❌ **Don't use Rename-Item:**
```powershell
Rename-Item "old_name.py" "new_name.py"
```

✅ **Use git mv:**
```bash
git mv old_name.py new_name.py
```

## If You Already Used Move-Item/Rename-Item:

If you accidentally used PowerShell commands:

1. **Check git status:**
   ```bash
   git status
   ```

2. **Add the new files:**
   ```bash
   git add new/location/file.py
   ```

3. **Remove the old files if Git shows them as deleted:**
   ```bash
   git rm old/location/file.py
   ```

4. **Git will usually detect the rename automatically in the commit**

## For this project:

The SMTP files were moved correctly and are now in their proper locations:
- ✅ `tests/test_smtp.py` - Testing utility
- ✅ `scripts/configure_smtp.py` - Configuration wizard
- ✅ `backend/SMTP_SETUP_GUIDE.md` - Documentation

All files have been added to Git properly.
