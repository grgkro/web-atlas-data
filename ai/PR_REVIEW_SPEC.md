# AI Pull Request Review Specification

This document defines how automated reviews evaluate pull requests
that add or modify website entries.

## Goals
- Keep Web Atlas useful, calm, and spam-free
- Scale curation without human gatekeeping
- Be transparent and explain decisions
- Prevent prompt injection attacks through strict input validation

## Submission Process for New Sites

### Secure URL-Only Submission

To prevent prompt injection attacks, new site submissions must follow a secure format:

1. **User submits PR with `.github/submissions.txt`**: Create or edit `.github/submissions.txt` containing one URL per line (max 200 characters per line)
   - Example:
     ```
     https://example.com
     https://another-site.org
     ```
   - Each line must be a valid HTTP/HTTPS URL

2. **Automated format validation** (script-based, not AI):
   - Validates that each line is a valid HTTP/HTTPS URL
   - Validates that each line does not exceed 200 characters
   - This validation happens BEFORE any AI processing to prevent prompt injection

3. **AI generation**: If validation passes, the AI:
   - Reads URLs from `.github/submissions.txt`
   - Fetches and analyzes each website
   - Generates complete `sites/<id>/site.yml` files with all required fields (id, category, lenses, quality, title, description, etc.)
   - Validates the generated data against the schema

4. **Auto-commit and cleanup**: If generation succeeds:
   - The generated `sites/<id>/site.yml` files are committed automatically to the PR branch
   - Processed URLs are removed from `.github/submissions.txt` (or the file is deleted if all URLs were processed)
   - The PR is marked as approved and ready for merge

This process ensures that:
- Users cannot inject malicious prompts into the AI system (AI only processes clean URLs)
- The `sites/` directory never contains invalid states (only complete, validated site files)
- Subsequent workflow runs skip processing if no URLs remain in `.github/submissions.txt`

### Editing Existing Sites

When editing existing `site.yml` files (not URL-only submissions), the standard review process applies with full AI review of all changes.

## Rejection Criteria
A submission MUST be rejected if it is:
- Scam, phishing, or malware
- Primarily affiliate or SEO spam
- Pornographic or NSFW
- Illegal or promoting harm
- Non-functional or deceptive

## Acceptance Criteria
A submission SHOULD be accepted if it:
- Serves a clear purpose
- Is reasonably usable
- Is not a low-effort clone
- Would be genuinely recommended to someone

## Categorization Rules
- Every website has exactly one primary category
- Categories should be simple and human-readable
- New categories are allowed but discouraged unless necessary

## Quality Bands
- exceptional: unusually high quality or unique
- solid: reliable, useful, established
- niche: useful for a specific audience

## Transparency
Every decision must include a short explanation in the PR.
