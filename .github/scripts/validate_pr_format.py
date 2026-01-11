#!/usr/bin/env python3
"""
Validate that PRs containing new site submissions follow the correct format.

New site submissions must be added to .github/submissions.txt as a single URL per line.
Each URL must be:
- A single line (max 200 characters)
- A valid HTTP/HTTPS URL
"""

import os
import re
import sys
from typing import Tuple

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_pr_context() -> Tuple[str, int]:
    """Get repository and PR number from environment."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number_str = os.environ.get("GITHUB_EVENT_PULL_REQUEST_NUMBER") or os.environ.get(
        "GITHUB_EVENT_NUMBER", ""
    )
    if not repo or not pr_number_str:
        # Fallback: parse from GITHUB_EVENT_PATH if available
        import json
        event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        if event_path and os.path.exists(event_path):
            with open(event_path, "r", encoding="utf-8") as f:
                event = json.load(f)
            repo = event.get("repository", {}).get("full_name", "")
            pr_number = event.get("pull_request", {}).get("number") or event.get("number")
            if repo and pr_number:
                return repo, int(pr_number)
        raise ValueError("Could not determine repository or PR number")
    return repo, int(pr_number_str)


def get_submissions_file() -> str:
    """Get the path to the submissions file."""
    return ".github/submissions.txt"


def validate_submissions_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that submissions.txt contains only valid URLs (one per line, max 200 chars each).
    Returns (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"Submissions file does not exist: {filepath}"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = [line.rstrip('\n\r') for line in content.splitlines()]
    
    # Check each line
    errors = []
    for i, line in enumerate(lines, start=1):
        url_line = line.strip()
        
        # Skip empty lines
        if not url_line:
            continue
        
        # Check length
        if len(url_line) > 200:
            errors.append(f"Line {i}: URL exceeds 200 characters (found {len(url_line)} chars)")
            continue
        
        # Check it looks like a URL
        url_lower = url_line.lower()
        if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
            errors.append(f"Line {i}: Must be a valid HTTP/HTTPS URL")
            continue
        
        # Basic URL format check (must have domain)
        if not re.match(r"https?://[^\s/]+", url_line):
            errors.append(f"Line {i}: Invalid URL format")
    
    if errors:
        return False, "Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
    
    return True, ""


def main() -> int:
    """Main validation function. Returns 0 on success, 1 on failure."""
    try:
        repo, pr_number = get_pr_context()
        submissions_file = get_submissions_file()
        
        # Check if submissions file was added/modified in this PR
        import subprocess
        
        # Get base commit
        base = subprocess.check_output(["git", "merge-base", "origin/main", "HEAD"], text=True).strip()
        
        # Check if submissions file was changed
        changed_files = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...HEAD"], text=True
        ).splitlines()
        
        submissions_changed = any(f.strip() == submissions_file for f in changed_files)
        
        if not submissions_changed:
            # No submissions file changed, validation passes
            print(f"✅ No changes to {submissions_file}, validation passed.")
            return 0
        
        # Validate the submissions file
        is_valid, error_msg = validate_submissions_file(submissions_file)
        
        if not is_valid:
            print(f"❌ Validation failed for {submissions_file}:")
            print(error_msg)
            
            # Post comment to PR
            import requests
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            }
            comment_body = f"""## ❌ PR Format Validation Failed

The submissions file `{submissions_file}` contains invalid entries:

{error_msg}

**Required format:**
- One URL per line
- Each URL must be HTTP/HTTPS and max 200 characters
- Example:
  ```
  https://example.com
  https://another-site.org
  ```
"""
            url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
            requests.post(url, headers=headers, json={"body": comment_body})
            
            return 1
        
        print(f"✅ Validation passed for {submissions_file}")
        return 0
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
