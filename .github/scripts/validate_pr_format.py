#!/usr/bin/env python3
"""
Validate that PRs follow the secure submission format.

For contributor PRs: Only .github/submissions.txt is allowed
For bot-result PRs: Only sites/<id>/site.yml and .github/submissions.txt deletion are allowed
"""

import json
import os
import re
import subprocess
import sys
from typing import List, Tuple

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def sh(cmd: List[str]) -> str:
    """Run shell command and return output."""
    return subprocess.check_output(cmd, text=True).strip()


def get_pr_context() -> Tuple[str, int, str]:
    """Get repository, PR number, and PR author from environment."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not set")
    
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    
    pr = event.get("pull_request", {})
    pr_number = int(pr.get("number", 0))
    pr_author = pr.get("user", {}).get("login", "")
    
    return repo, pr_number, pr_author


def get_changed_files() -> List[str]:
    """Get list of all changed files in this PR."""
    base = sh(["git", "merge-base", "origin/main", "HEAD"])
    out = sh(["git", "diff", "--name-only", f"{base}...HEAD"])
    return [f.strip() for f in out.splitlines() if f.strip()]


def validate_submissions_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that submissions.txt contains exactly one valid URL (max 200 chars).
    Returns (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"Submissions file does not exist: {filepath}"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = [line.rstrip('\n\r') for line in content.splitlines()]
    
    # Filter out empty lines and comments
    url_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    
    if len(url_lines) != 1:
        return False, f"Submissions file must contain exactly one URL, found {len(url_lines)}"
    
    url_line = url_lines[0]
    
    # Check length
    if len(url_line) > 200:
        return False, f"URL exceeds 200 characters (found {len(url_line)} chars)"
    
    # Check it looks like a URL
    url_lower = url_line.lower()
    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        return False, "Must be a valid HTTP/HTTPS URL"
    
    # Basic URL format check (must have domain)
    if not re.match(r"https?://[^\s/]+", url_line):
        return False, "Invalid URL format"
    
    return True, ""


def is_allowed_for_maintainer(filepath: str) -> bool:
    """Check if file is in allowed paths for maintainers (workflow/script changes)."""
    allowed_maintainer_paths = [
        ".github/workflows/",
        ".github/scripts/",
        "schemas/",
        "ai/",
    ]
    return any(filepath.startswith(path) for path in allowed_maintainer_paths)


def main() -> int:
    """Main validation function. Returns 0 on success, 1 on failure."""
    try:
        repo, pr_number, pr_author = get_pr_context()
        
        # Allow maintainer to modify workflows/scripts (for development)
        # TODO: Replace with actual maintainer username or use GitHub teams
        is_maintainer = pr_author in ["grgkro"]  # Add more maintainers as needed
        
        changed_files = get_changed_files()
        
        if not changed_files:
            print("✅ No files changed, validation passed.")
            return 0
        
        # Check if submissions.txt exists and has content
        submissions_file = ".github/submissions.txt"
        has_submissions = os.path.exists(submissions_file)
        submissions_valid = False
        if has_submissions:
            submissions_valid, _ = validate_submissions_file(submissions_file)
        
        # Determine if this is a contributor PR or bot-result PR
        is_contributor_pr = has_submissions and submissions_valid
        
        # Check if PR is from bot (using authenticated GitHub identity from event payload, not spoofable git author)
        # SECURITY: We use pr_author (from GitHub event payload) instead of git commit author because
        # git commit author fields can be spoofed locally. The GitHub event payload pr_author is
        # authenticated and cannot be spoofed by contributors.
        BOT_USERNAME = "web-atlas-bot"
        is_bot_pr = pr_author == BOT_USERNAME
        
        # Get base commit for checking what files are actually new
        base = sh(["git", "merge-base", "origin/main", "HEAD"])
        new_site_files = [
            f for f in changed_files
            if re.match(r'^sites/[^/]+/site\.yml$', f) and
            f in sh(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"]).splitlines()
        ]
        
        # Validate file changes based on PR type
        errors = []
        warnings = []
        
        # Build allowed files list based on PR type
        if is_contributor_pr:
            # Case 1: Contributor submission PR
            # Only allow .github/submissions.txt
            allowed_files = {submissions_file}
            pr_type = "contributor submission"
        elif not has_submissions and new_site_files and is_bot_pr:
            # Case 2: Bot result PR
            # Allow sites/<id>/site.yml, .github/submissions.txt (deletion)
            allowed_files = set()
            for f in changed_files:
                if re.match(r'^sites/[^/]+/site\.yml$', f):
                    allowed_files.add(f)
                elif f == submissions_file:
                    allowed_files.add(f)  # Allow deletion/modification
            pr_type = "bot result"
        else:
            # Unknown/invalid PR type
            allowed_files = set()  # No files allowed for invalid PR type
            errors.append(f"Invalid PR type: submissions.txt exists={has_submissions}, valid={submissions_valid}, bot_pr={is_bot_pr}, new_site_files={len(new_site_files)}")
            pr_type = "invalid"
        
        # Check for disallowed files (unless maintainer)
        for filepath in changed_files:
            if filepath in allowed_files:
                continue
            
            # Allow maintainer to modify workflows/scripts
            if is_maintainer and is_allowed_for_maintainer(filepath):
                warnings.append(f"⚠️ Maintainer change (allowed): {filepath}")
                continue
            
            # Everything else is disallowed
            errors.append(f"❌ Disallowed file change: {filepath}")
        
        # Additional validation for contributor PRs
        if is_contributor_pr:
            # Validate submissions.txt format
            is_valid, error_msg = validate_submissions_file(submissions_file)
            if not is_valid:
                errors.append(f"❌ {submissions_file}: {error_msg}")
        
        # Report results
        if errors:
            error_text = "\n".join(errors)
            print(f"❌ PR format validation failed ({pr_type} PR):")
            print(error_text)
            
            # Post comment to PR
            try:
                import requests
                headers = {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                }
                comment_body = f"""## ❌ PR Format Validation Failed

This PR does not follow the secure submission format.

**Errors:**
{error_text}

**For contributor PRs:** Only `.github/submissions.txt` with exactly one URL is allowed.

**For bot-result PRs:** Only `sites/<id>/site.yml` files and `.github/submissions.txt` deletion are allowed. Bot-result PRs must be created by the `web-atlas-bot` account.

**Disallowed changes:** Workflow files, scripts, schemas, or AI files cannot be modified in submission PRs.
"""
                url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
                requests.post(url, headers=headers, json={"body": comment_body}, timeout=10)
            except Exception as e:
                print(f"Warning: Could not post PR comment: {e}")
            
            return 1
        
        if warnings:
            print("\n".join(warnings))
        
        print(f"✅ PR format validation passed ({pr_type} PR)")
        return 0
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
