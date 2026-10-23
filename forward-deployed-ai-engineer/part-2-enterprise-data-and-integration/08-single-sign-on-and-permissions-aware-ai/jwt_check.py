# jwt_check.py: check an ID token properly. Every line here prevents a real attack.
#
# A JWT ("JSON Web Token", say "jot") is three base64url parts joined by dots:  HEADER.PAYLOAD.SIGNATURE
#   header   {"alg": "RS256", "kid": "..."}               which algorithm and key signed it
#   payload  {"iss": ..., "aud": ..., "sub": "alice", "groups": [...], "exp": ...}   the "claims"
#   signature  made with the identity provider's PRIVATE key; checked with its PUBLIC key from /jwks
# Anyone can READ a JWT (it's only encoded, not encrypted). Only the provider can SIGN one.
import jwt

ALLOWED_ALGORITHMS = ["RS256"]   # never accept "none", and never let the token choose the algorithm


class TokenError(Exception):
    pass


def public_key_for(token, jwks):
    """Find the public key whose 'kid' matches the token's header."""
    try:
        kid = jwt.get_unverified_header(token).get("kid")          # reading the header before checking is OK
    except jwt.PyJWTError as error:
        raise TokenError(f"not a JWT: {error}") from None
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return jwt.PyJWK(key).key
    raise TokenError(f"unknown key id {kid!r} (keys rotated? fetch /jwks again)")


def validate_id_token(token, jwks, issuer, audience, nonce=None, leeway=30):
    """Return the claims if the token is genuine and meant for us; raise TokenError otherwise."""
    key = public_key_for(token, jwks)
    try:
        claims = jwt.decode(token, key, algorithms=ALLOWED_ALGORITHMS,
                            audience=audience,                       # issued for OUR app, not another one
                            issuer=issuer,                           # issued by OUR identity provider
                            leeway=leeway,                           # allow 30 s of clock difference
                            options={"require": ["exp", "iat", "iss", "aud", "sub"]})
    except jwt.ExpiredSignatureError:
        raise TokenError("token expired") from None
    except jwt.InvalidAudienceError:
        raise TokenError("token was issued for another app (wrong audience)") from None
    except jwt.InvalidIssuerError:
        raise TokenError("token was issued by another provider (wrong issuer)") from None
    except jwt.InvalidSignatureError:
        raise TokenError("signature check failed (token forged or changed)") from None
    except jwt.PyJWTError as error:
        raise TokenError(f"invalid token: {error}") from None
    if nonce is not None and claims.get("nonce") != nonce:
        raise TokenError("nonce mismatch (token replayed from another login)")
    return claims
