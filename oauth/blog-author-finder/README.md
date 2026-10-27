# find_author_posts.sh

Finds a specific author's blog post on a PortSwigger-Academy-style blog (`/post?postId=N`) by scanning post IDs and grepping the byline (`<span id=blog-author>...</span>`) for a given name.

## Origin

Built while working through **Lab: Forced OAuth profile linking** (OAuth 2.0 authentication, PortSwigger Web Security Academy). Wanted a fast way to locate which `postId` belonged to a given author rather than clicking through the blog index by hand. Turned out not to be needed for that lab's actual solution (the linking vulnerability is a CSRF issue on the OAuth-linking endpoint, unrelated to blog post authorship) — but it's a reusable recon helper for any target running this blog layout, so it's kept here rather than thrown away.

## Usage

```bash
chmod +x find_author_posts.sh
./find_author_posts.sh TARGET_DOMAIN "AUTHOR_NAME"
```

Example:
```bash
./find_author_posts.sh 0a040029034892d1800417c400b800f9.web-security-academy.net "Sam"
# postId=2 -> Sam Pit -> https://0a040029034892d1800417c400b800f9.web-security-academy.net/post?postId=2
```

Optional third argument overrides the post-ID scan range (default `1-20`):
```bash
./find_author_posts.sh TARGET_DOMAIN "AUTHOR_NAME" 50
```

## Notes

- Matching is case-insensitive and substring-based (`"sam"` matches `Sam Pit`).
- Only works against blogs using the exact `<span id=blog-author>Name</span>` byline markup. For a different blog platform/layout, the `grep -oP` pattern needs updating to match that site's actual author markup — view-source one post first.
- Brute-forces sequential `postId` values; doesn't discover IDs dynamically. For a site where IDs aren't small sequential integers, pull the ID list from the sitemap or blog index first instead.
- No rate limiting built in — add a `sleep` between requests if running against anything but a local lab.

## Dependencies

None beyond `curl` and GNU `grep` with PCRE support (`-P`). Git Bash on Windows (GNU grep for Windows) has this; if your `grep` errors with `invalid option -- P`, swap the extraction for `sed` instead.
