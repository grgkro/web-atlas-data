# AI Pull Request Review Specification

This document defines how automated reviews evaluate pull requests
that add or modify website entries.

## Goals
- Keep Web Atlas useful, calm, and spam-free
- Scale curation without human gatekeeping
- Be transparent and explain decisions

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
