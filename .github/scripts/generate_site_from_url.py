#!/usr/bin/env python3
"""
Generate site.yml files from URL-only submissions in .github/submissions.txt.

This script is run as a separate job to generate site files without committing.
The workflow job handles the commit and push.
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

import requests
import yaml
from jsonschema import Draft202012Validator

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ENABLE_URL_FETCH = os.environ.get("ENABLE_URL_FETCH", "true").lower() == "true"

def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def get_pr_context() -> Tuple[str, int]:
    """Get repository and PR number from environment."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number_str = os.environ.get("GITHUB_EVENT_PULL_REQUEST_NUMBER") or os.environ.get(
        "GITHUB_EVENT_NUMBER", ""
    )
    if not repo or not pr_number_str:
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

def read_submissions_file(filepath: str = ".github/submissions.txt") -> List[str]:
    """Read URLs from submissions file, returning list of URLs (one per line, skipping empty lines)."""
    if not os.path.exists(filepath):
        return []
    
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith("#"):  # Skip empty lines and comments
                urls.append(url)
    return urls

def write_submissions_file(filepath: str, urls: List[str]) -> None:
    """Write URLs to submissions file (one per line)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")

def is_probably_bad_url(url: str) -> bool:
    """Basic heuristic to catch obviously bad URLs."""
    u = url.lower()
    if not (u.startswith("https://") or u.startswith("http://")):
        return True
    bad_patterns = [
        r"^https?://localhost",
        r"^https?://127\.0\.0\.1",
        r"^https?://0\.0\.0\.0",
        r"^https?://.*\.local",
    ]
    return any(re.search(p, u) for p in bad_patterns)

def head_check(url: str) -> Tuple[bool, str]:
    """Check if URL is reachable via HEAD request."""
    if not ENABLE_URL_FETCH:
        return True, "skipped"
    try:
        r = requests.head(url, timeout=8, allow_redirects=True)
        if r.status_code >= 400:
            return False, f"HTTP {r.status_code}"
        return True, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def generate_slug_from_url(url: str) -> str:
    """Generate a slug ID from a URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    if domain.startswith("www."):
        domain = domain[4:]
    slug = re.sub(r'[^a-z0-9]+', '-', domain.lower())
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug[:50]

def load_site_schema_validator() -> Draft202012Validator:
    schema = load_yaml("schemas/site.schema.json")
    return Draft202012Validator(schema)

def load_policy() -> Dict[str, Any]:
    return load_yaml("ai/policy.yml")

def load_allowed_categories() -> List[str]:
    doc = load_yaml("ai/policy.yml")
    return doc.get("categories", [])

def load_allowed_lenses() -> List[str]:
    doc = load_yaml("ai/policy.yml")
    return doc.get("lenses", [])

def openai_chat(prompt: str) -> Dict[str, Any]:
    """Call OpenAI API and return JSON response."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI error {r.status_code}: {r.text}")
    return r.json()

def generate_site_yml_from_url(url: str, policy: Dict[str, Any], allowed_categories: List[str], allowed_lenses: List[str]) -> Dict[str, Any]:
    """Use AI to generate a full site.yml entry from a URL."""
    url_content = ""
    try:
        if ENABLE_URL_FETCH:
            r = requests.get(url, timeout=10, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                import re
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', r.text, re.IGNORECASE)
                if title_match:
                    url_content = f"Page title: {title_match.group(1)[:200]}"
    except Exception:
        pass
    
    prompt_text = f"""Generate a complete site.yml entry for a website directory from a URL. You must return your response as valid JSON.

URL: {url}
{("Page preview: " + url_content) if url_content else ""}

Policy: {json.dumps(policy, indent=2)}

Allowed categories: {', '.join(allowed_categories)}
Allowed lenses: {', '.join(allowed_lenses)}

Instructions:
1. Analyze the URL to understand what the website is
2. Generate id as a slug from the domain (e.g., 'example-com' from 'example.com')
3. Choose the most appropriate category from the allowed list
4. Select 0-4 relevant lenses from the allowed list
5. Assess quality: exceptional (unusually high quality), solid (reliable/established), or niche (specific audience)
6. Write a clear, factual title
7. Write a one-sentence description (max 160 chars), factual, no marketing fluff

Return your response as a JSON object with these fields:
- id (string): slug identifier (lowercase, hyphens only)
- url (string): the provided URL
- category (string): MUST be exactly one of these values: {', '.join(allowed_categories)}. Do not invent new categories.
- lenses (array of strings, 0-4 items): from allowed lenses: {', '.join(allowed_lenses)}
- quality (string): "exceptional", "solid", or "niche"
- title (object): {{"en": "English title"}}
- description (object): {{"en": "English description"}}

IMPORTANT: The category field MUST be exactly one of: {', '.join(allowed_categories)}. Use "Knowledge" for educational content, books, documentation, references, etc.

Return ONLY valid JSON, no markdown formatting, no code blocks."""
    
    try:
        resp = openai_chat(prompt_text)
        content = resp["choices"][0]["message"]["content"]
        result = json.loads(content)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to generate site.yml from URL: {e}")


def main() -> int:
    """Main function. Returns 0 on success, 1 on failure."""
    try:
        repo, pr_number = get_pr_context()
        submissions_file = ".github/submissions.txt"
        
        # Read URLs from submissions file
        urls = read_submissions_file(submissions_file)
        
        if not urls:
            print("No URLs in submissions file, skipping generation.")
            return 0
        
        print(f"Found {len(urls)} URL(s) in {submissions_file}")
        
        policy = load_policy()
        allowed_categories = load_allowed_categories()
        allowed_lenses = load_allowed_lenses()
        site_validator = load_site_schema_validator()
        
        # Check all existing site files for URL duplicates
        all_site_files = []
        sites_dir = "sites"
        if os.path.exists(sites_dir):
            for site_id in os.listdir(sites_dir):
                site_file = os.path.join(sites_dir, site_id, "site.yml")
                if os.path.exists(site_file):
                    all_site_files.append(site_file)
        
        site_url_index: Dict[str, List[str]] = {}
        for sf in all_site_files:
            try:
                data = load_yaml(sf)
                if isinstance(data, dict) and "url" in data:
                    url = normalize_url(str(data["url"]))
                    site_url_index.setdefault(url, []).append(sf)
            except Exception:
                pass
        
        errors = []
        generated_files = []
        processed_urls = []
        remaining_urls = []
        
        for url in urls:
            normalized_url = normalize_url(url)
            site_id = generate_slug_from_url(normalized_url)
            site_file = os.path.join(sites_dir, site_id, "site.yml")
            
            # Skip if site already exists
            if os.path.exists(site_file):
                errors.append(f"- ⚠️ `{url}`: Site already exists at {site_file}")
                remaining_urls.append(url)  # Keep in submissions file
                continue
            
            # Check for duplicates
            if normalized_url in site_url_index:
                errors.append(f"- ⚠️ `{url}`: URL already exists in: {', '.join(site_url_index[normalized_url])}")
                remaining_urls.append(url)  # Keep in submissions file
                continue
            
            try:
                site_data = generate_site_yml_from_url(url, policy, allowed_categories, allowed_lenses)
                
                # Validate generated data
                errs = sorted(site_validator.iter_errors(site_data), key=lambda er: er.path)
                if errs:
                    error_msgs = "; ".join([f"{'.'.join(str(p) for p in er.path) if er.path else 'root'}: {er.message}" for er in errs])
                    errors.append(f"- ❌ `{url}`: Generated data has schema errors: {error_msgs}")
                    remaining_urls.append(url)  # Keep in submissions file
                    continue
                
                # Double-check category is in allowed list (schema validation should catch this, but be explicit)
                if site_data.get("category") not in allowed_categories:
                    errors.append(f"- ❌ `{url}`: Category '{site_data.get('category')}' is not in allowed list: {', '.join(allowed_categories)}")
                    remaining_urls.append(url)  # Keep in submissions file
                    continue
                
                # Check URL
                if is_probably_bad_url(normalized_url):
                    errors.append(f"- ❌ `{url}`: URL looks invalid/suspicious: `{normalized_url}`")
                    remaining_urls.append(url)  # Keep in submissions file
                    continue
                
                ok, info = head_check(normalized_url)
                if not ok:
                    errors.append(f"- ❌ `{url}`: URL check failed: {info}")
                    remaining_urls.append(url)  # Keep in submissions file
                    continue
                
                # Save generated site.yml
                save_yaml(site_file, site_data)
                # Verify file was written
                if os.path.exists(site_file):
                    with open(site_file, "r", encoding="utf-8") as f:
                        written_content = f.read()
                    if len(written_content) > 50:  # Should be much more than just a URL
                        generated_files.append(site_file)
                        processed_urls.append(url)  # Mark as processed (will be removed from submissions)
                        print(f"✅ Generated: {site_file} ({len(written_content)} chars)")
                    else:
                        errors.append(f"- ❌ `{url}`: File written but content too short (only {len(written_content)} chars)")
                        remaining_urls.append(url)  # Keep in submissions file
                else:
                    errors.append(f"- ❌ `{url}`: File was not written")
                    remaining_urls.append(url)  # Keep in submissions file
                
            except Exception as e:
                errors.append(f"- ❌ `{url}`: Error generating site.yml: {e}")
                remaining_urls.append(url)  # Keep in submissions file
        
        if errors:
            print("\n".join(errors))
            print("\n❌ Site generation failed. Please check the URLs and try again.")
            
            # Update submissions file to keep only unprocessed URLs
            if remaining_urls != urls:  # Only update if some URLs were processed
                write_submissions_file(submissions_file, remaining_urls)
            
            return 1
        
        if generated_files:
            print(f"\n✅ Successfully generated {len(generated_files)} site file(s).")
            
            # Remove processed URLs from submissions file (write remaining URLs, or delete if empty)
            if remaining_urls:
                write_submissions_file(submissions_file, remaining_urls)
            else:
                # All URLs processed, delete the file
                if os.path.exists(submissions_file):
                    os.remove(submissions_file)
                    print(f"✅ Removed {submissions_file} (all URLs processed)")
            
            # Write list of generated files for the workflow to commit
            with open(".github/generated_sites.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(generated_files))
                if remaining_urls:  # Also note if submissions file was updated
                    f.write("\n")
                    f.write(submissions_file)
            return 0
        else:
            print("No URLs processed, skipping generation.")
            return 0
        
    except Exception as e:
        print(f"❌ Site generation error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
