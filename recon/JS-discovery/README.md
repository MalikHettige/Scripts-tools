# JavaScript Discovery and Response Analysis

## Objective
Discover JavaScript resources referenced by a target's HTML and use them to understand client-side functionality, application workflows, and potentially exposed information.

## Procedure

1. Capture the target page's HTTP response.
2. Extract script URLs from its HTML.
3. Resolve relative URLs against the correct origin.
4. Decode HTML entities such as `&amp;`.
5. Deduplicate URLs and record the source page.
6. Fetch relevant JavaScript files and inspect their contents.
7. Search for route paths, API endpoints, parameter names, feature flags, and application-specific configuration.
8. Record interesting findings and validate them against the authorized program scope.

## Example extraction command

```bash
curl -sL 'https://TARGET.example/' |
grep -oE '<script[^>]+src="[^"]+"' |
grep -oE 'src="[^"]+"' |
cut -d '"' -f 2 |
sort -u
```

Note: this simple pipeline handles only certain HTML formats. An HTML parser is more reliable for single-quoted attributes, additional attributes, and HTML entity decoding.

## What to record

| Field | Description |
|---|---|
| Source page | Page containing the script reference |
| Script URL | Resolved JavaScript URL |
| Hostname | Host serving the resource |
| Script type | First-party, third-party, vendor, or unknown |
| Interesting clues | Routes, API references, configuration, or exposed data |
| Scope status | In scope, out of scope, or unverified |
| Follow-up | What needs further investigation |

## Important distinctions

- A discovered hostname is not automatically an in-scope target.
- A route string in JavaScript does not prove that the endpoint exists or is accessible.
- Client-side configuration is not automatically a secret.
- Record observations separately from hypotheses and confirmed vulnerabilities.

## Success criteria

Produce a deduplicated JavaScript inventory, understand the purpose of relevant scripts, and identify evidence-based follow-up questions.
