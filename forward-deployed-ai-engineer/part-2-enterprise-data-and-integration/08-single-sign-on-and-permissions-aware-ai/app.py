# app.py: the Northwind assistant with single sign-on and permission-aware answers.
#
#   (terminal 1)  uvicorn mock_idp:app --port 9000
#   (terminal 2)  uvicorn app:app --port 8300           then open http://127.0.0.1:8300
#
# Login uses OpenID Connect (authorization code flow + PKCE). Answers use ONLY documents the signed-in user's
# groups may read. With no AI configured, it shows the permitted sources instead of an AI answer.
import base64
import hashlib
import html
import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import llm
from acl_search import search
from jwt_check import TokenError, validate_id_token

IDP_URL = os.getenv("IDP_URL", "http://127.0.0.1:9000")
CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "northwind-assistant")
CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "assistant-oidc-secret-change-me")
REDIRECT_URI = os.getenv("OIDC_REDIRECT_URI", "http://127.0.0.1:8300/callback")

app = FastAPI(title="Northwind assistant (SSO)")
idp_http = httpx.Client(base_url=IDP_URL, timeout=10)     # talks to the identity provider (tests swap it)
PENDING = {}     # state -> {nonce, code_verifier}: logins that have started but not finished
SESSIONS = {}    # session id (in the browser's cookie) -> the user's verified claims
_idp_config = {}


def idp():
    """Fetch the provider's discovery document and public keys once, then reuse them."""
    if not _idp_config:
        _idp_config.update(idp_http.get("/.well-known/openid-configuration").json())
        _idp_config["jwks"] = idp_http.get(_idp_config["jwks_uri"].replace(IDP_URL, "")).json()
    return _idp_config


def current_user(session_id):
    user = SESSIONS.get(session_id or "")
    if not user:
        raise HTTPException(401, "not signed in: go to /login")
    return user


@app.get("/login")
def login():
    state = secrets.token_urlsafe(16)            # ties the callback to THIS login (stops forged callbacks, CSRF)
    nonce = secrets.token_urlsafe(16)            # ties the ID token to THIS login (stops token replay)
    verifier = secrets.token_urlsafe(48)         # PKCE secret: stays here; only its hash goes to the browser
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    PENDING[state] = {"nonce": nonce, "code_verifier": verifier}
    params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "scope": "openid",
              "state": state, "nonce": nonce, "code_challenge": challenge, "code_challenge_method": "S256"}
    return RedirectResponse(f"{idp()['authorization_endpoint']}?{urlencode(params)}", status_code=303)


@app.get("/callback")
def callback(code: str, state: str):
    login_attempt = PENDING.pop(state, None)
    if not login_attempt:
        raise HTTPException(400, "unknown or reused state: start again at /login")
    response = idp_http.post("/token", auth=(CLIENT_ID, CLIENT_SECRET), data={
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
        "code_verifier": login_attempt["code_verifier"]})       # proves we started this login
    if response.status_code != 200:
        raise HTTPException(401, f"sign-in failed: {response.json()}")
    try:
        claims = validate_id_token(response.json()["id_token"], idp()["jwks"], issuer=idp()["issuer"],
                                   audience=CLIENT_ID, nonce=login_attempt["nonce"])
    except TokenError as reason:
        raise HTTPException(401, f"sign-in failed: {reason}")
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = claims
    page = RedirectResponse("/", status_code=303)
    # HttpOnly: page scripts can't read the cookie. SameSite=Lax: other sites can't send it with their forms.
    # In production also set secure=True (HTTPS only).
    page.set_cookie("session", session_id, httponly=True, samesite="lax", max_age=8 * 3600)
    return page


@app.get("/logout")
def logout(session: str = Cookie(None)):
    SESSIONS.pop(session or "", None)
    page = RedirectResponse("/", status_code=303)
    page.delete_cookie("session")
    return page


@app.get("/", response_class=HTMLResponse)
def home(session: str = Cookie(None)):
    user = SESSIONS.get(session or "")
    if not user:
        return "<html><body style='font-family:sans-serif'><h2>Northwind assistant</h2>" \
               "<a href='/login'>Sign in with Northwind SSO</a></body></html>"
    return (f"<html><body style='font-family:sans-serif'><h2>Hi {html.escape(user['name'])}</h2>"
            f"<p>Your groups: {html.escape(', '.join(user['groups']))} · <a href='/logout'>sign out</a></p>"
            "<form action='/ask'><input name='q' size='60' placeholder='Ask about Northwind policies'>"
            "<button>Ask</button></form></body></html>")


SYSTEM = ("Answer the employee's question using ONLY the documents given. Cite document ids like [DOC-1]. "
          "If the documents don't contain the answer, say you don't have that information.")


@app.get("/ask")
def ask(q: str, session: str = Cookie(None)):
    user = current_user(session)
    sources = search(q, user["groups"])                         # permission filter happens inside search()
    context = "\n\n".join(f"[{d['id']}] {d['title']}\n{d['text']}" for d in sources)
    try:
        answer = llm.ask(f"<documents>\n{context or 'NO DOCUMENTS'}\n</documents>\n\nQuestion: {q}", system=SYSTEM)
        mode = "ai"
    except (Exception, SystemExit) as problem:                  # no key / no Ollama: still useful, still safe
        answer = "AI unavailable (" + str(problem).split(". ")[0] + "). Documents you may read: " + \
                 ("; ".join(f"[{d['id']}] {d['title']}" for d in sources) or "none match your question")
        mode = "sources_only"
    print(f"[ask] user={user['sub']} groups={user['groups']} sources={[d['id'] for d in sources]}")  # ids, not text
    return {"user": user["sub"], "groups": user["groups"], "mode": mode,
            "sources": [{"id": d["id"], "title": d["title"]} for d in sources], "answer": answer}
