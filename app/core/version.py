"""
Dynamic version management based on Git commits.
Automatically increments version on each commit.
"""
import subprocess
from typing import Optional


def get_git_version() -> str:
    """
    Get version from Git tags and commits.
    
    Format: MAJOR.MINOR.PATCH-COMMITS-HASH
    Example: 1.0.0-5-a1b2c3d
    
    Returns:
        Version string or fallback version
    """
    try:
        # Get the latest git tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        version = result.stdout.strip()
        
        # If no tags exist, use commit count as version
        if not version or "-" not in version:
            commit_count = get_commit_count()
            commit_hash = get_commit_hash()
            version = f"0.1.{commit_count}-{commit_hash}"
        
        return version
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Fallback if git is not available or not a git repo
        return get_fallback_version()


def get_commit_count() -> int:
    """Get total number of commits in the repository."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return 0


def get_commit_hash() -> str:
    """Get short commit hash (7 characters)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def get_fallback_version() -> str:
    """Fallback version when Git is not available."""
    return "1.0.0-dev"


# Cache the version at module import
__version__ = get_git_version()
