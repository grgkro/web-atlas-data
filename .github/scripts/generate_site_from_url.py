#!/usr/bin/env python3
"""
Generate site.yml files from URL-only submissions.

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
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def sh(cmd: List[str]) -> str:
    import subprocess
    return subprocess.check_output(cmd, text=True).strip()

def get_pr_context() -> Tuple[str, int]:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not set")
    
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = int(event["pull_request"]["number"])
    return repo, pr_number

def git_changed_site_files() -> List[str]:
    """Get list of changed site.yml files in this PR."""
    base = sh(["git", "merge-base", "origin/main", "HEAD"])
    out = sh(["git", "diff", "--name-only", f"{base}...HEAD"])
    changed = [p for p in out.splitlines() if re.match(r"sites/[^/]+/site\.ya?ml$", p)]
    return changed

def is_url_only_file(filepath: str) -> Tuple[bool, str]:
    """Check if a site.yml file contains only a URL."""
    if not os.path.exists(filepath):
        return False, ""
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = [line.rstrip('\n\r') for line in content.splitlines() if line.strip()]
    
    if len(lines) != 1:
        return False, ""
    
    url_line = lines[0].strip()
    url_lower = url_line.lower()
    if url_lower.startswith("http://") or url_lower.startswith("https://"):
        if len(url_line) <= 200:
            return True, url_line
    
    return False, ""

def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")

def is_probably_bad_url(url: str) -> bool:
    u = url.lower()
    if not (u.startswith("https://") or u.startswith("http://")):
        return True
    bad_patterns = [
        r"free-money",
        r"get-rich-quick",
        r"casino",
        r"porn",
        r"xxx",
        r"crack",
        r"keygen",
    ]
    return any(re.search(p, u) for p in bad_patterns)

def head_check(url: str) -> Tuple[bool, str]:
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
    try:
        from urllib.parse import urlparse
    except ImportError:
        import urlparse
        urlparse = urlparse.urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    if domain.startswith("www."):
        domain = domain[4:]
    slug = re.sub(r'[^a-z0-9]+', '-', domain.lower())
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug[:50]

def load_site_schema_validator() -> Draft202012Validator:
    schema = json.load(open("schemas/site.schema.json", "r", encoding="utf-8"))
    return Draft202012Validator(schema)

def load_policy() -> Dict[str, Any]:
    return load_yaml("ai/policy.yml")

def load_allowed_categories() -> List[str]:
    doc = load_yaml("ai/categories.yml")
    return doc.get("categories", [])

def load_allowed_lenses() -> List[str]:
    doc = load_yaml("ai/lenses.yml")
    return doc.get("lenses", [])

def openai_chat(prompt: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You are a strict but fair reviewer for an open-source website directory."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code >= 400:
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
- category (string): one of {', '.join(allowed_categories)}
- lenses (array of strings, 0-4 items): from allowed lenses
- quality (string): "exceptional", "solid", or "niche"
- title (object): {{"en": "English title"}}
- description (object): {{"en": "One sentence description, max 160 chars"}}

Required fields: id, url, category, title, description"""

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
        changed_site_files = git_changed_site_files()
        
        if not changed_site_files:
            print("No site files changed, skipping generation.")
            return 0
        
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
        
        for site_file in changed_site_files:
            is_url_only, url = is_url_only_file(site_file)
            if not is_url_only:
                continue  # Skip non-URL-only files
            
            try:
                site_data = generate_site_yml_from_url(url, policy, allowed_categories, allowed_lenses)
                
                # Validate generated data
                errs = sorted(site_validator.iter_errors(site_data), key=lambda er: er.path)
                if errs:
                    errors.append(f"- ❌ `{site_file}`: Generated data has schema errors: " + "; ".join([er.message for er in errs]))
                    continue
                
                # Check for duplicates
                normalized_url = normalize_url(site_data.get("url", ""))
                if normalized_url in site_url_index:
                    errors.append(f"- ⚠️ `{site_file}`: URL already exists in: {', '.join(site_url_index[normalized_url])}")
                    continue
                
                # Check URL
                if is_probably_bad_url(normalized_url):
                    errors.append(f"- ❌ `{site_file}`: URL looks invalid/suspicious: `{normalized_url}`")
                    continue
                
                ok, info = head_check(normalized_url)
                if not ok:
                    errors.append(f"- ❌ `{site_file}`: URL check failed: {info}")
                    continue
                
                # Save generated site.yml
                save_yaml(site_file, site_data)
                generated_files.append(site_file)
                print(f"✅ Generated: {site_file}")
                
            except Exception as e:
                errors.append(f"- ❌ `{site_file}`: Error generating site.yml: {e}")
        
        if errors:
            print("\n".join(errors))
            print("\n❌ Site generation failed. Please check the URLs and try again.")
            return 1
        
        if generated_files:
            print(f"\n✅ Successfully generated {len(generated_files)} site file(s).")
            # Write list of generated files for the workflow to commit
            with open(".github/generated_sites.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(generated_files))
            return 0
        else:
            print("No URL-only site files found, skipping generation.")
            return 0
        
    except Exception as e:
        print(f"❌ Site generation error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

