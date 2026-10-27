# mock_idp.py: a tiny pretend identity provider (like Microsoft Entra ID, Okta or Google), speaking OpenID Connect.
#
#   uvicorn mock_idp:app --port 9000
#
# It does the four things a real one does:
#   /.well-known/openid-configuration   "here are my addresses" (discovery)
#   /authorize                          the sign-in page; afterwards it sends the browser back with a one-time code
#   /token                              swaps that code for an ID token (a signed JWT saying who the user is)
#   /jwks                               the PUBLIC keys anyone can use to check the signature on ID tokens
# Real providers ask for a password and MFA. This one just lets you pick a user: it's for learning only.
import base64
import hashlib
import html
import os
import secrets
import time
from urllib.parse import urlencode

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

ISSUER = os.getenv("IDP_ISSUER", "http://127.0.0.1:9000")
app = FastAPI(title="Northwind identity provider (mock)")

# A fresh RSA key pair every start. The PRIVATE key signs tokens and never leaves this server.
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KEY_ID = secrets.token_hex(4)                      # "kid": tells verifiers which public key to use

USERS = {   # the company directory: who exists and which groups they are in
    "alice": {"name": "Alice Jansen", "email": "alice@northwind.example", "groups": ["staff", "support"]},
    "frank": {"name": "Frank de Vries", "email": "frank@northwind.example", "groups": ["staff", "finance"]},
    "carol": {"name": "Carol Nowak", "email": "carol@northwind.example", "groups": ["staff", "claims"]},
    "dana": {"name": "Dana Okafor", "email": "dana@northwind.example", "groups": ["staff", "management"]},
}
CLIENTS = {  # apps registered with this provider ("app registrations" in Entra ID)
    "northwind-assistant": {"secret": "assistant-oidc-secret-change-me",
                            "redirect_uris": ["http://127.0.0.1:8300/callback"]},
}
CODES = {}   # one-time authorization codes waiting to be swapped for tokens


@app.get("/.well-known/openid-configuration")
def discovery():
    return {"issuer": ISSUER, "authorization_endpoint": f"{ISSUER}/authorize", "token_endpoint": f"{ISSUER}/token",
            "jwks_uri": f"{ISSUER}/jwks", "response_types_supported": ["code"],
            "id_token_signing_alg_values_supported": ["RS256"], "code_challenge_methods_supported": ["S256"]}


@app.get("/jwks")
def jwks():
    key = jwt.algorithms.RSAAlgorithm.to_jwk(PRIVATE_KEY.public_key(), as_dict=True)   # public half only
    return {"keys": [{**key, "kid": KEY_ID, "use": "sig", "alg": "RS256"}]}


@app.get("/authorize", response_class=HTMLResponse)
def authorize(client_id: str, redirect_uri: str, state: str, nonce: str, code_challenge: str,
              response_type: str = "code", scope: str = "openid", code_challenge_method: str = "S256"):
    client = CLIENTS.get(client_id)
    if not client or redirect_uri not in client["redirect_uris"]:
        raise HTTPException(400, "unknown client or redirect_uri not registered")   # never redirect to strangers
    if response_type != "code" or code_challenge_method != "S256" or "openid" not in scope.split():
        raise HTTPException(400, "only the authorization code flow with PKCE S256 is supported")
    hidden = "".join(f'<input type="hidden" name="{k}" value="{html.escape(v)}">' for k, v in
                     {"client_id": client_id, "redirect_uri": redirect_uri, "state": state, "nonce": nonce,
                      "code_challenge": code_challenge}.items())
    buttons = "".join(f'<button name="user" value="{u}">{html.escape(i["name"])} ({", ".join(i["groups"])})'
                      f'</button><br>' for u, i in USERS.items())
    return (f"<html><body style='font-family:sans-serif'><h2>Northwind sign-in (mock)</h2>"
            f"<p>A real provider asks for a password and MFA here. Pick a user:</p>"
            f"<form method='post' action='/authorize/login'>{hidden}{buttons}</form></body></html>")


@app.post("/authorize/login")
def login(user: str = Form(...), client_id: str = Form(...), redirect_uri: str = Form(...), state: str = Form(...),
          nonce: str = Form(...), code_challenge: str = Form(...)):
    client = CLIENTS.get(client_id)
    if user not in USERS or not client or redirect_uri not in client["redirect_uris"]:
        raise HTTPException(400, "bad sign-in request")
    code = secrets.token_urlsafe(24)
    CODES[code] = {"user": user, "client_id": client_id, "redirect_uri": redirect_uri, "nonce": nonce,
                   "code_challenge": code_challenge, "expires_at": time.time() + 60}     # codes live 1 minute
    return RedirectResponse(f"{redirect_uri}?{urlencode({'code': code, 'state': state})}", status_code=303)


def pkce_challenge(verifier):
    """S256: base64url(sha256(verifier)) without '=' padding. The app sends this at /authorize, the verifier at /token."""
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


@app.post("/token")
def token(grant_type: str = Form(...), code: str = Form(...), redirect_uri: str = Form(...),
          code_verifier: str = Form(...), basic: HTTPBasicCredentials = Depends(HTTPBasic())):
    error = lambda e: JSONResponse({"error": e}, status_code=400)
    client = CLIENTS.get(basic.username)
    if not client or not secrets.compare_digest(client["secret"], basic.password):
        return JSONResponse({"error": "invalid_client"}, status_code=401)
    if grant_type != "authorization_code":
        return error("unsupported_grant_type")
    grant = CODES.pop(code, None)                                  # pop: a code works exactly once
    if not grant or grant["expires_at"] < time.time():
        return error("invalid_grant")
    if grant["client_id"] != basic.username or grant["redirect_uri"] != redirect_uri:
        return error("invalid_grant")
    if not secrets.compare_digest(pkce_challenge(code_verifier), grant["code_challenge"]):
        return error("invalid_grant")                              # PKCE: a stolen code alone is useless
    person, now = USERS[grant["user"]], int(time.time())
    claims = {"iss": ISSUER, "aud": basic.username, "sub": grant["user"], "name": person["name"],
              "email": person["email"], "groups": person["groups"], "nonce": grant["nonce"],
              "iat": now, "exp": now + 300}
    id_token = jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": KEY_ID})
    return {"id_token": id_token, "token_type": "Bearer", "expires_in": 300}
