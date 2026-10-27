#!/usr/bin/env bash
# find_author_posts.sh — find a blog post by a specific author, by scanning postId values
#
# Usage:
#   ./find_author_posts.sh TARGET_DOMAIN "AUTHOR_NAME"
#
# Example:
#   ./find_author_posts.sh example.com "Sam"
#
# Matching is case-insensitive and substring-based, so "sam" matches "Sam Pit".

set -uo pipefail

DOMAIN="${1:?Usage: $0 TARGET_DOMAIN \"AUTHOR_NAME\"}"
AUTHOR="${2:?Usage: $0 TARGET_DOMAIN \"AUTHOR_NAME\"}"
AUTHOR_LC="${AUTHOR,,}"

# Adjust the range if the target has more/fewer posts than this covers.
MAX_POST_ID="${3:-20}"

for id in $(seq 1 "$MAX_POST_ID"); do
  url="https://$DOMAIN/post?postId=$id"
  found=$(curl -s "$url" | grep -oP '(?<=<span id=blog-author>).*?(?=</span>)')
  [ -z "$found" ] && continue

  found_lc="${found,,}"
  if [[ "$found_lc" == *"$AUTHOR_LC"* ]]; then
    echo "postId=$id -> $found -> $url"
  fi
done
