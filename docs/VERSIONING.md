# Dynamic Versioning Guide

## How It Works

Your service version now **automatically updates** based on Git commits!

### Version Format

```
MAJOR.MINOR.PATCH-COMMITS-HASH
```

**Examples:**
- `1.0.0-15-a1b2c3d` - Version 1.0.0, 15 commits since tag, commit hash a1b2c3d
- `0.1.25-f4e3d2c` - No tags, 25 total commits, commit hash f4e3d2c

---

## Setup Instructions

### 1. **Initialize Git Versioning** (First Time)

```bash
# Create your first version tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

### 2. **Normal Development Workflow**

Every commit automatically increments the version:

```bash
# Make changes
git add .
git commit -m "Add new feature"
git push

# Version automatically becomes: 1.0.0-1-abc1234
```

### 3. **Create New Releases**

When you want to bump the version:

```bash
# Minor version bump (1.0.0 → 1.1.0)
git tag -a v1.1.0 -m "New features"
git push origin v1.1.0

# Major version bump (1.1.0 → 2.0.0)
git tag -a v2.0.0 -m "Breaking changes"
git push origin v2.0.0

# Patch version bump (1.1.0 → 1.1.1)
git tag -a v1.1.1 -m "Bug fixes"
git push origin v1.1.1
```

---

## Where Version Appears

### 1. **API Documentation** (`/docs`)
- Shows in Swagger UI header
- Visible to all API users

### 2. **Observability Logs**
Every log event includes the version:
```json
{
  "service": {
    "name": "badminton_api",
    "version": "1.0.0-5-a1b2c3d"
  }
}
```

### 3. **Health Check** (Optional - can add)
```bash
curl http://localhost:8000/health
# Returns: {"version": "1.0.0-5-a1b2c3d", ...}
```

---

## Benefits

✅ **Automatic** - No manual version updates  
✅ **Traceable** - Know exact commit for each deployment  
✅ **Debugging** - Logs show exact version running  
✅ **Rollback** - Easy to identify which version to revert to  

---

## Example Workflow

```bash
# Day 1: Initial release
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
# Version: 1.0.0

# Day 2: Add feature
git commit -m "Add tournament filtering"
git push
# Version: 1.0.0-1-abc1234

# Day 3: Add another feature
git commit -m "Add player search"
git push
# Version: 1.0.0-2-def5678

# Day 4: Release new version
git tag -a v1.1.0 -m "New features"
git push origin v1.1.0
# Version: 1.1.0

# Day 5: Bug fix
git commit -m "Fix search bug"
git push
# Version: 1.1.0-1-ghi9012
```

---

## Checking Current Version

### In Code:
```python
from app.core.version import __version__
print(__version__)  # 1.0.0-5-a1b2c3d
```

### In Terminal:
```bash
# See current version
git describe --tags --always

# See all tags
git tag -l
```

### In Logs:
Check your observability database - every event has the version!

---

## Troubleshooting

**No version showing?**
```bash
# Create initial tag
git tag -a v1.0.0 -m "Initial version"
git push origin v1.0.0
```

**Version shows "1.0.0-dev"?**
- Not a Git repository
- Git not installed
- Fallback version used

**Want to change version format?**
Edit `app/core/version.py` and customize the `get_git_version()` function.

---

## Production Deployment

On Render, the version will be automatically set based on the deployed commit:
- Each deployment shows exact version
- Easy to track which code is running
- Logs include version for debugging

Perfect for production monitoring! 🚀
