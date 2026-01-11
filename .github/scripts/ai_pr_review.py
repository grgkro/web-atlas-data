import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import requests
import yaml
from jsonschema import Draft202012Validator

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
REVIEW_MODE = os.environ.get("REVIEW_MODE", "comment-only")  # comment-only | autofix
ENABLE_URL_FETCH = os.environ.get("ENABLE_URL_FETCH", "true").lower() == "true"

# -----------------------------
# Helpers
# -----------------------------

def sh(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def get_pr_context() -> Tuple[str, int, str]:
    # PR info from GitHub Actions env
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = int(os.environ.get("GITHUB_REF", "").split("/")[-1]) if False else None  # not reliable
    # Better: use event payload
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    pr_number = int(event["pull_request"]["number"])
    sha = event["pull_request"]["head"]["sha"]
    return repo, pr_number, sha

def gh_api(method: str, url: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.request(method, url, headers=headers, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub API error {r.status_code}: {r.text}")
    return r.json() if r.text else {}

def post_pr_comment(repo: str, pr_number: int, body: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    gh_api("POST", url, {"body": body})

def list_changed_files(repo: str, pr_number: int) -> List[str]:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files?per_page=100"
    files = []
    page = 1
    while True:
        page_url = url + f"&page={page}"
        res = requests.get(
            page_url,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if res.status_code >= 400:
            raise RuntimeError(f"GitHub API error {res.status_code}: {res.text}")
        batch = res.json()
        if not batch:
            break
        for f in batch:
            files.append(f["filename"])
        page += 1
    return files

def git_changed_category_files() -> List[str]:
    # Local diff is easier and faster than API in most cases.
    base = sh(["git", "merge-base", "origin/main", "HEAD"])
    out = sh(["git", "diff", "--name-only", f"{base}...HEAD"])
    changed = [p for p in out.splitlines() if p.startswith("categories/") and (p.endswith(".yml") or p.endswith(".yaml"))]
    return changed

def git_changed_site_files() -> List[str]:
    """Get list of changed site.yml files in this PR."""
    base = sh(["git", "merge-base", "origin/main", "HEAD"])
    out = sh(["git", "diff", "--name-only", f"{base}...HEAD"])
    changed = [p for p in out.splitlines() if re.match(r"sites/[^/]+/site\.ya?ml$", p)]
    return changed

def is_url_only_file(filepath: str) -> Tuple[bool, str]:
    """
    Check if a site.yml file contains only a URL (URL-only submission).
    Returns (is_url_only, url_or_error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = [line.rstrip('\n\r') for line in content.splitlines() if line.strip()]
    
    # Must have exactly one non-empty line
    if len(lines) != 1:
        return False, ""
    
    url_line = lines[0].strip()
    
    # Check it looks like a URL
    url_lower = url_line.lower()
    if url_lower.startswith("http://") or url_lower.startswith("https://"):
        if len(url_line) <= 200:  # Should have been validated already, but double-check
            return True, url_line
    
    return False, ""

def generate_slug_from_url(url: str) -> str:
    """Generate a slug ID from a URL."""
    try:
        from urllib.parse import urlparse
    except ImportError:
        # Fallback for older Python versions (shouldn't happen in 3.11+)
        import urlparse
        urlparse = urlparse.urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    # Take domain and convert to slug
    slug = re.sub(r'[^a-z0-9]+', '-', domain.lower())
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug[:50]  # Limit length

def generate_site_yml_from_url(url: str, policy: Dict[str, Any], allowed_categories: List[str], allowed_lenses: List[str]) -> Dict[str, Any]:
    """
    Use AI to generate a full site.yml entry from a URL.
    Returns the generated site data as a dict.
    """
    # Fetch URL to get content for AI
    url_content = ""
    try:
        if ENABLE_URL_FETCH:
            r = requests.get(url, timeout=10, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                # Extract text content (simplified - just get title from HTML)
                import re
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', r.text, re.IGNORECASE)
                if title_match:
                    url_content = f"Page title: {title_match.group(1)[:200]}"
    except Exception:
        pass  # Continue without content
    
    # Generate slug
    slug = generate_slug_from_url(url)
    
    # Build a text prompt that explicitly mentions JSON (required by OpenAI API)
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

def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")

def is_probably_bad_url(url: str) -> bool:
    u = url.lower()
    if not (u.startswith("https://") or u.startswith("http://")):
        return True
    # hard-block obvious junk patterns (tweak over time)
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

# -----------------------------
# Schema / Policy
# -----------------------------

def load_schema_validator() -> Draft202012Validator:
    schema = json.load(open("schema/website.schema.json", "r", encoding="utf-8"))
    return Draft202012Validator(schema)

def load_site_schema_validator() -> Draft202012Validator:
    schema = json.load(open("schemas/site.schema.json", "r", encoding="utf-8"))
    return Draft202012Validator(schema)

def load_policy() -> Dict[str, Any]:
    # Keep policy in-repo so changes are versioned
    return load_yaml("ai/policy.yml")

def load_allowed_lenses() -> List[str]:
    doc = load_yaml("ai/lenses.yml")
    return doc.get("lenses", [])

def load_allowed_categories() -> List[str]:
    doc = load_yaml("ai/categories.yml")
    return doc.get("categories", [])

# -----------------------------
# Diff parsing: find added/changed entries
# -----------------------------

@dataclass
class EntryRef:
    file_path: str
    index: int
    entry: Dict[str, Any]

def parse_yaml_list_file(path: str) -> List[Dict[str, Any]]:
    data = load_yaml(path)
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a YAML list of website entries")
    for i, e in enumerate(data):
        if not isinstance(e, dict):
            raise ValueError(f"{path}: entry {i} is not a mapping/object")
    return data

def build_url_index(all_files: List[str]) -> Dict[str, List[Tuple[str, int]]]:
    index: Dict[str, List[Tuple[str, int]]] = {}
    for fp in all_files:
        entries = parse_yaml_list_file(fp)
        for i, e in enumerate(entries):
            u = normalize_url(str(e.get("url", "")))
            if not u:
                continue
            index.setdefault(u, []).append((fp, i))
    return index

def get_all_category_files() -> List[str]:
    out = sh(["bash", "-lc", "ls -1 categories/*.y*ml 2>/dev/null || true"])
    files = [x.strip() for x in out.splitlines() if x.strip()]
    return files

# -----------------------------
# LLM call (OpenAI)
# -----------------------------

def openai_chat(prompt: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    # Minimal direct HTTP call; swap to official SDK if you prefer.
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4.1-mini",
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

def build_llm_prompt(
    policy: Dict[str, Any],
    allowed_categories: List[str],
    allowed_lenses: List[str],
    changed_entries: List[EntryRef],
    url_checks: Dict[str, str],
) -> str:
    entries_payload = []
    for ref in changed_entries:
        entries_payload.append({
            "file": ref.file_path,
            "index": ref.index,
            "entry": ref.entry
        })

    prompt = {
        "policy": policy,
        "allowed_categories": allowed_categories,
        "allowed_lenses": allowed_lenses,
        "changed_entries": entries_payload,
        "url_checks": url_checks,
        "instructions": {
            "task": "Decide accept/reject per entry; if accept, propose normalized fields and corrected categorization.",
            "output_json_schema": {
                "type": "object",
                "required": ["summary", "decisions"],
                "properties": {
                    "summary": {"type": "string"},
                    "decisions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["file", "index", "action", "reason"],
                            "properties": {
                                "file": {"type": "string"},
                                "index": {"type": "integer"},
                                "action": {"type": "string", "enum": ["accept", "reject", "needs_changes"]},
                                "reason": {"type": "string"},
                                "proposed_entry": {"type": "object"},
                                "suggested_category": {"type": "string"},
                                "suggested_lenses": {"type": "array", "items": {"type": "string"}},
                                "quality": {"type": "string", "enum": ["exceptional", "solid", "niche"]}
                            }
                        }
                    }
                }
            },
            "hard_rules": [
                "Reject scams, malware, phishing, NSFW, illegal content, hate/harassment.",
                "Reject obvious SEO/affiliate spam or low-effort clones.",
                "If category is not allowed, propose the closest allowed category.",
                "Only use lenses from allowed_lenses; propose at most 4 lenses.",
                "Description max 160 chars; one sentence; no marketing fluff."
            ]
        }
    }
    return json.dumps(prompt, ensure_ascii=False, indent=2)

# -----------------------------
# Apply fixes (optional)
# -----------------------------

def apply_autofix(decisions: List[Dict[str, Any]]) -> bool:
    touched = False
    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for d in decisions:
        if d.get("action") != "accept":
            continue
        proposed = d.get("proposed_entry")
        if not proposed:
            continue
        by_file.setdefault(d["file"], []).append(d)

    for fp, items in by_file.items():
        entries = parse_yaml_list_file(fp)
        for d in items:
            idx = d["index"]
            if idx < 0 or idx >= len(entries):
                continue
            entries[idx] = d["proposed_entry"]
            touched = True
        save_yaml(fp, entries)

    return touched

def commit_changes(message: str, files: List[str] | None = None) -> None:
    sh(["git", "status", "--porcelain"])
    sh(["git", "config", "user.name", "web-atlas-bot"])
    sh(["git", "config", "user.email", "web-atlas-bot@users.noreply.github.com"])
    if files:
        for f in files:
            sh(["git", "add", f])
    else:
        sh(["git", "add", "categories"])
    sh(["git", "commit", "-m", message])
    sh(["git", "push"])

# -----------------------------
# Main
# -----------------------------

def main() -> None:
    repo, pr_number, sha = get_pr_context()

    # Load policy and constraints (needed for both site and category processing)
    policy = load_policy()
    allowed_categories = load_allowed_categories()
    allowed_lenses = load_allowed_lenses()

    # ===== Process URL-only site submissions =====
    changed_site_files = git_changed_site_files()
    url_only_sites_processed = False
    
    if changed_site_files:
        site_validator = load_site_schema_validator()
        site_errors = []
        generated_files = []
        
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
        
        for site_file in changed_site_files:
            is_url_only, url = is_url_only_file(site_file)
            if is_url_only:
                url_only_sites_processed = True
                try:
                    # Generate full site.yml from URL
                    site_data = generate_site_yml_from_url(url, policy, allowed_categories, allowed_lenses)
                    
                    # Validate generated data
                    errs = sorted(site_validator.iter_errors(site_data), key=lambda er: er.path)
                    if errs:
                        site_errors.append(f"- ❌ `{site_file}`: Generated data has schema errors: " + "; ".join([er.message for er in errs]))
                        continue
                    
                    # Check for duplicates
                    normalized_url = normalize_url(site_data.get("url", ""))
                    if normalized_url in site_url_index:
                        site_errors.append(f"- ⚠️ `{site_file}`: URL already exists in: {', '.join(site_url_index[normalized_url])}")
                        continue
                    
                    # Check URL
                    if is_probably_bad_url(normalized_url):
                        site_errors.append(f"- ❌ `{site_file}`: URL looks invalid/suspicious: `{normalized_url}`")
                        continue
                    
                    ok, info = head_check(normalized_url)
                    if not ok:
                        site_errors.append(f"- ❌ `{site_file}`: URL check failed: {info}")
                        continue
                    
                    # Save generated site.yml
                    save_yaml(site_file, site_data)
                    generated_files.append(site_file)
                    
                except Exception as e:
                    site_errors.append(f"- ❌ `{site_file}`: Error generating site.yml: {e}")
        
        if site_errors:
            body = "## 🤖 AI Site Generation Failed\n\n" + "\n".join(site_errors) + "\n\nPlease check the URLs and try again."
            post_pr_comment(repo, pr_number, body)
            return
        
        if generated_files:
            # Commit generated site.yml files
            try:
                commit_changes("chore: AI generate site.yml from URL submissions", generated_files)
                post_pr_comment(repo, pr_number, f"## ✅ AI Generated Site Files\n\nGenerated complete site.yml files for {len(generated_files)} site(s). The PR is ready for review/merge.")
                # Mark as approved since we generated and validated
                os.makedirs(".github/ai_review", exist_ok=True)
                with open(".github/ai_review/APPROVED", "w", encoding="utf-8") as f:
                    f.write("approved")
                return  # Done with URL-only submissions
            except Exception as e:
                post_pr_comment(repo, pr_number, f"## ⚠️ AI Site Generation Issue\n\nGenerated site files but could not commit: `{e}`")
                return
        
        # If there are site files but none were URL-only, continue with normal review below
        # (site files with full YAML will be reviewed normally, but we don't have that logic yet)
    
    # ===== Process category files (existing logic) =====
    changed_files = git_changed_category_files()
    if not changed_files:
        if not url_only_sites_processed:
            post_pr_comment(repo, pr_number, "✅ AI review: no category or site files changed.")
        return

    validator = load_schema_validator()

    # Build global URL index for duplicates
    all_files = get_all_category_files()
    url_index = build_url_index(all_files)

    # For now: review all entries in changed files (simple, deterministic).
    # Later optimization: parse diff hunks to isolate only newly added items.
    changed_entries: List[EntryRef] = []
    local_errors: List[str] = []
    url_checks: Dict[str, str] = {}

    for fp in changed_files:
        try:
            entries = parse_yaml_list_file(fp)
        except Exception as e:
            local_errors.append(f"- ❌ `{fp}`: YAML parse error: {e}")
            continue

        for i, e in enumerate(entries):
            # validate required schema fields for each entry
            errs = sorted(validator.iter_errors(e), key=lambda er: er.path)
            if errs:
                local_errors.append(f"- ❌ `{fp}` entry #{i}: schema errors: " + "; ".join([er.message for er in errs]))
                continue

            url = normalize_url(str(e.get("url", "")))
            if is_probably_bad_url(url):
                local_errors.append(f"- ❌ `{fp}` entry #{i}: url looks invalid/suspicious: `{url}`")
                continue

            # duplicates across repo
            locs = url_index.get(url, [])
            if len(locs) > 1:
                local_errors.append(f"- ⚠️ duplicate url `{url}` found in: " + ", ".join([f"{a}[{b}]" for a, b in locs]))

            ok, info = head_check(url)
            url_checks[url] = ("ok: " if ok else "fail: ") + info

            changed_entries.append(EntryRef(fp, i, e))

    if local_errors:
        body = "## 🤖 AI review (pre-checks)\n\n" + "\n".join(local_errors) + "\n\nFix these and the AI will re-review."
        post_pr_comment(repo, pr_number, body)
        return

    # LLM review
    prompt = build_llm_prompt(policy, allowed_categories, allowed_lenses, changed_entries, url_checks)
    try:
        resp = openai_chat(prompt)
        content = resp["choices"][0]["message"]["content"]
        result = json.loads(content)
    except Exception as e:
        post_pr_comment(repo, pr_number, f"## 🤖 AI review failed\n\nError calling AI reviewer: `{e}`")
        return

    decisions = result.get("decisions", [])
    summary = result.get("summary", "(no summary)")

    # Build PR comment
    lines = ["## 🤖 AI review", "", summary, ""]
    any_reject = False
    any_needs_changes = False
    any_accept = False

    for d in decisions:
        action = d.get("action", "needs_changes")
        fp = d.get("file", "?")
        idx = d.get("index", -1)
        reason = d.get("reason", "")
        if action == "reject":
            any_reject = True
            emoji = "❌"
        elif action == "needs_changes":
            any_needs_changes = True
            emoji = "⚠️"
        else:
            any_accept = True
            emoji = "✅"
        lines.append(f"- {emoji} `{fp}` entry #{idx}: **{action}** — {reason}")

        if action != "reject":
            sc = d.get("suggested_category")
            sl = d.get("suggested_lenses")
            q = d.get("quality")
            if sc or sl or q:
                lines.append(f"  - suggested: category=`{sc}` lenses=`{sl}` quality=`{q}`")

    if REVIEW_MODE == "autofix" and any_accept and not any_reject:
        touched = apply_autofix(decisions)
        if touched:
            try:
                commit_changes("chore: AI normalize entries")
                lines.append("\n✅ I pushed normalization fixes to this PR branch.")
            except Exception as e:
                lines.append(f"\n⚠️ Autofix prepared but could not push commit: `{e}`")

    post_pr_comment(repo, pr_number, "\n".join(lines))

    # Mark approved for downstream merge step (only if fully clean)
    os.makedirs(".github/ai_review", exist_ok=True)
    if any_reject or any_needs_changes:
        # ensure APPROVED not present
        try:
            os.remove(".github/ai_review/APPROVED")
        except FileNotFoundError:
            pass
    else:
        with open(".github/ai_review/APPROVED", "w", encoding="utf-8") as f:
            f.write("approved")

if __name__ == "__main__":
    main()
