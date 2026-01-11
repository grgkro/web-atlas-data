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

1. **User submits PR with URL-only file**: Create `sites/<site-id>/site.yml` containing exactly one line with the website URL (max 200 characters)
   - Example: `https://example.com`
   - The file must contain only the URL, nothing else

2. **Automated format validation** (script-based, not AI):
   - Validates that the file contains exactly one line
   - Validates that the line is a valid HTTP/HTTPS URL
   - Validates that the line does not exceed 200 characters
   - This validation happens BEFORE any AI processing to prevent prompt injection

3. **AI generation**: If validation passes, the AI:
   - Fetches and analyzes the website
   - Generates a complete `site.yml` file with all required fields (id, category, lenses, quality, title, description, etc.)
   - Validates the generated data against the schema

4. **Auto-commit and approval**: If generation succeeds:
   - The complete `site.yml` is committed automatically to the PR branch
   - The PR is marked as approved and ready for merge

This process ensures that users cannot inject malicious prompts into the AI system, as the AI only processes clean URLs and generates all metadata itself.

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
