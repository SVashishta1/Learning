# signing.py: sign and verify webhook messages with HMAC-SHA256 (the same idea Stripe, GitHub and Slack use).
#
# The sender and the receiver share one secret. The sender computes a "signature" from the secret, the time
# and the exact bytes of the message, and puts it in a header:
#     X-Northwind-Signature: t=1792569600,v1=5f2c...e9
# The receiver recomputes it. If the message was changed, or sent by someone without the secret,
# the signatures don't match. The timestamp stops an attacker from replaying an old, valid message later.
import hashlib
import hmac
import time

HEADER = "X-Northwind-Signature"
TOLERANCE_SECONDS = 300          # accept messages signed at most 5 minutes ago (or ahead, for clock drift)


def sign(secret, body, timestamp=None):
    """Return the header value for this body. body must be the exact bytes that will be sent."""
    timestamp = int(time.time() if timestamp is None else timestamp)
    message = f"{timestamp}.".encode() + body                     # sign the time AND the body together
    digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def verify(secret, header, body, now=None, tolerance=TOLERANCE_SECONDS):
    """Raise ValueError with a reason if the signature is missing, wrong or too old. Return True if fine."""
    if not header:
        raise ValueError("missing signature header")
    try:
        parts = dict(item.split("=", 1) for item in header.split(","))
        timestamp, received = int(parts["t"]), parts["v1"]
    except (KeyError, ValueError):
        raise ValueError("malformed signature header") from None
    now = time.time() if now is None else now
    if abs(now - timestamp) > tolerance:
        raise ValueError("signature timestamp too old (possible replay)")
    expected = sign(secret, body, timestamp).split("v1=")[1]
    if not hmac.compare_digest(expected, received):               # constant-time compare: no timing leaks
        raise ValueError("signature does not match")
    return True
