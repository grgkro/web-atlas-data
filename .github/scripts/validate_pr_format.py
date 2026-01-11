#!/usr/bin/env python3
"""
Validation script to check PR format for new site submissions.

For new sites, PRs must only add site.yml files with a single line (max 200 chars)
containing just the website URL. This prevents prompt injection attacks.

This script runs BEFORE AI review and uses simple text parsing (no AI/LM calls).
"""

import os
import re
import subprocess
import sys
from typing import List, Tuple

def sh(cmd: List[str]) -> str:
    """Run shell command and return output."""
    return subprocess.check_output(cmd, text=True).strip()

def get_pr_context() -> Tuple[str, int]:
    """Get repository and PR number from GitHub Actions environment."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not set")
    
    import json
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    pr_number = int(event["pull_request"]["number"])
    return repo, pr_number

def get_new_site_files() -> List[str]:
    """Get list of new site.yml files added in this PR."""
    base = sh(["git", "merge-base", "origin/main", "HEAD"])
    # Get added files (not modified or deleted)
    out = sh(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"])
    new_files = []
    for line in out.splitlines():
        line = line.strip()
        # Match sites/*/site.yml pattern
        if re.match(r"sites/[^/]+/site\.ya?ml$", line):
            new_files.append(line)
    return new_files

def validate_site_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that a site.yml file contains only a URL (single line, max 200 chars).
    Returns (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = [line.rstrip('\n\r') for line in content.splitlines() if line.strip()]
    
    # Must have exactly one non-empty line
    if len(lines) != 1:
        return False, f"File must contain exactly one line, found {len(lines)} lines"
    
    url_line = lines[0].strip()
    
    # Check length
    if len(url_line) > 200:
        return False, f"URL line exceeds 200 characters (found {len(url_line)} chars)"
    
    # Check it looks like a URL
    url_lower = url_line.lower()
    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        return False, "Line must be a valid HTTP/HTTPS URL"
    
    # Basic URL format check (must have domain)
    if not re.match(r"https?://[^\s/]+", url_line):
        return False, "Invalid URL format"
    
    return True, ""

def main() -> int:
    """Main validation function. Returns 0 on success, 1 on failure."""
    try:
        new_site_files = get_new_site_files()
        
        if not new_site_files:
            # No new site files, validation passes (might be editing existing sites or category files)
            print("✅ No new site files to validate.")
            return 0
        
        errors = []
        for filepath in new_site_files:
            is_valid, error_msg = validate_site_file(filepath)
            if not is_valid:
                errors.append(f"❌ `{filepath}`: {error_msg}")
        
        if errors:
            repo, pr_number = get_pr_context()
            # Post comment to PR
            try:
                import requests
                import json
                
                github_token = os.environ.get("GITHUB_TOKEN", "")
                if github_token:
                    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
                    headers = {
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    }
                    body = "## 🔒 PR Format Validation Failed\n\n" + "\n".join(errors) + "\n\n**Requirements for new sites:**\n- File must contain exactly one line\n- Line must be a valid URL (max 200 characters)\n- Example: `https://example.com`"
                    requests.post(url, headers=headers, json={"body": body}, timeout=10)
            except Exception as e:
                print(f"Warning: Could not post PR comment: {e}")
            
            print("\n".join(errors))
            print("\n❌ PR format validation failed. Please fix the errors above.")
            return 1
        
        print(f"✅ Validation passed for {len(new_site_files)} new site file(s).")
        return 0
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

