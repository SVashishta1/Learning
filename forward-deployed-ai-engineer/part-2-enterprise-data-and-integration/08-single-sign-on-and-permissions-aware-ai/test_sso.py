import re
import time
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

import acl_search
import app as assistant
import llm
import mock_idp
from fake_llm import FakeClaude
from jwt_check import TokenError, validate_id_token

ISSUER, AUDIENCE = mock_idp.ISSUER, "northwind-assistant"
JWKS = mock_idp.jwks()


def make_token(private_key=mock_idp.PRIVATE_KEY, kid=None, **overrides):
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "alice", "groups": ["staff", "support"], "nonce": "n1",
              "iat": now, "exp": now + 300, **overrides}
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": kid or mock_idp.KEY_ID})


# ---------- 1. token validation: every attack is refused ----------

def test_a_genuine_token_is_accepted():
    claims = validate_id_token(make_token(), JWKS, ISSUER, AUDIENCE, nonce="n1")
    assert claims["sub"] == "alice" and claims["groups"] == ["staff", "support"]


@pytest.mark.parametrize("token, reason", [
    (lambda: make_token(exp=int(time.time()) - 120), "expired"),
    (lambda: make_token(aud="some-other-app"), "wrong audience"),
    (lambda: make_token(iss="https://evil.example"), "wrong issuer"),
    (lambda: make_token(private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048)), "signature"),
    (lambda: make_token(nonce="other-login"), "nonce"),
    (lambda: make_token(kid="unknown"), "unknown key id"),
])
def test_bad_tokens_are_refused(token, reason):
    with pytest.raises(TokenError, match=reason):
        validate_id_token(token(), JWKS, ISSUER, AUDIENCE, nonce="n1")


def test_changed_payload_is_refused():
    header, payload, signature = make_token().split(".")
    claims = jwt.decode(make_token(), options={"verify_signature": False})
    claims["groups"] = ["management"]                                 # try to promote yourself
    forged_payload = jwt.utils.base64url_encode(jwt.utils.force_bytes(__import__("json").dumps(claims))).decode()
    with pytest.raises(TokenError, match="signature"):
        validate_id_token(f"{header}.{forged_payload}.{signature}", JWKS, ISSUER, AUDIENCE)


def test_unsigned_alg_none_token_is_refused():
    unsigned = jwt.encode({"iss": ISSUER, "aud": AUDIENCE, "sub": "x"}, key=None, algorithm="none",
                          headers={"kid": mock_idp.KEY_ID})
    with pytest.raises(TokenError):
        validate_id_token(unsigned, JWKS, ISSUER, AUDIENCE)


# ---------- 2. permissions: users only ever see what they may ----------

ACCESS = {  # who may read what: the rule the tests enforce
    "alice": {"DOC-1", "DOC-2"}, "frank": {"DOC-1", "DOC-3"},
    "carol": {"DOC-1", "DOC-4"}, "dana": {"DOC-1", "DOC-3", "DOC-4", "DOC-5"},
}


@pytest.mark.parametrize("user", ACCESS)
def test_every_user_sees_exactly_their_documents(user):
    groups = mock_idp.USERS[user]["groups"]
    for doc in acl_search.DOCUMENTS:
        found = {d["id"] for d in acl_search.search(doc["title"] + " " + doc["text"], groups, top_k=10)}
        assert (doc["id"] in found) == (doc["id"] in ACCESS[user]), (user, doc["id"])


def test_filter_happens_before_top_k():
    # 'delayed' appears in 3 documents. Restricted ones must not use up alice's top-1 slot.
    results = acl_search.search("delayed shipment", ["staff", "support"], top_k=1)
    assert [d["id"] for d in results] == ["DOC-1"]


# ---------- 3. the full login flow, through the real endpoints ----------

@pytest.fixture
def browser(monkeypatch):
    monkeypatch.setattr(assistant, "idp_http", TestClient(mock_idp.app, base_url=mock_idp.ISSUER))
    assistant._idp_config.clear()
    return TestClient(assistant.app)


def sign_in(browser, user):
    """Do what a browser does: /login -> IdP sign-in page -> pick user -> back to /callback."""
    to_idp = browser.get("/login", follow_redirects=False).headers["location"]
    idp = TestClient(mock_idp.app)
    page = idp.get(urlparse(to_idp).path + "?" + urlparse(to_idp).query).text
    hidden = dict(re.findall(r'type="hidden" name="(\w+)" value="([^"]*)"', page))
    back = idp.post("/authorize/login", data={**hidden, "user": user}, follow_redirects=False).headers["location"]
    query = parse_qs(urlparse(back).query)
    return browser.get("/callback", params={"code": query["code"][0], "state": query["state"][0]},
                       follow_redirects=False), query


def test_login_sets_a_session_and_answers_use_only_allowed_documents(browser, monkeypatch):
    fake = FakeClaude(text="Credit notes above 1,000 EUR need the CFO [DOC-3].")
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", fake)
    response, _ = sign_in(browser, "frank")
    assert response.status_code == 303 and "session" in response.cookies
    result = browser.get("/ask", params={"q": "credit note approval"}).json()
    assert result["user"] == "frank" and result["mode"] == "ai" and result["sources"][0]["id"] == "DOC-3"
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "CFO must approve" in prompt and "salary" not in prompt.lower()


def test_restricted_text_never_reaches_the_llm(browser, monkeypatch):
    fake = FakeClaude(text="I don't have that information.")
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", fake)
    sign_in(browser, "alice")
    result = browser.get("/ask", params={"q": "salary bands support agent 2027"}).json()
    sent = str(fake.calls)
    assert "34,000" not in sent and "Salary bands" not in sent           # DOC-5 is management only
    assert all(s["id"] != "DOC-5" for s in result["sources"])


def test_without_ai_it_still_answers_safely(browser, monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    sign_in(browser, "carol")
    result = browser.get("/ask", params={"q": "damage claims insurer"}).json()
    assert result["mode"] == "sources_only" and "[DOC-4] Claims handling procedure" in result["answer"]


def test_not_signed_in_is_refused(browser):
    assert browser.get("/ask", params={"q": "anything"}).status_code == 401


def test_callback_cannot_be_replayed_or_forged(browser):
    response, query = sign_in(browser, "alice")
    assert response.status_code == 303
    again = browser.get("/callback", params={"code": query["code"][0], "state": query["state"][0]})
    assert again.status_code == 400                                     # state is single-use
    assert browser.get("/callback", params={"code": "x", "state": "made-up"}).status_code == 400


def test_idp_refuses_reused_codes_and_wrong_pkce_verifier():
    idp = TestClient(mock_idp.app)
    challenge = mock_idp.pkce_challenge("the-real-verifier")
    form = {"client_id": AUDIENCE, "redirect_uri": "http://127.0.0.1:8300/callback", "state": "s",
            "nonce": "n", "code_challenge": challenge, "user": "alice"}
    code = parse_qs(urlparse(idp.post("/authorize/login", data=form, follow_redirects=False)
                             .headers["location"]).query)["code"][0]
    auth = (AUDIENCE, mock_idp.CLIENTS[AUDIENCE]["secret"])
    swap = {"grant_type": "authorization_code", "code": code, "redirect_uri": form["redirect_uri"]}
    assert idp.post("/token", auth=auth, data={**swap, "code_verifier": "stolen-code-no-verifier"}).status_code == 400
    code2 = parse_qs(urlparse(idp.post("/authorize/login", data=form, follow_redirects=False)
                              .headers["location"]).query)["code"][0]
    ok = idp.post("/token", auth=auth, data={**swap, "code": code2, "code_verifier": "the-real-verifier"})
    assert ok.status_code == 200 and "id_token" in ok.json()
    reused = idp.post("/token", auth=auth, data={**swap, "code": code2, "code_verifier": "the-real-verifier"})
    assert reused.json() == {"error": "invalid_grant"}


def test_idp_refuses_unregistered_redirect():
    response = TestClient(mock_idp.app).get("/authorize", params={
        "client_id": AUDIENCE, "redirect_uri": "https://evil.example/steal", "state": "s", "nonce": "n",
        "code_challenge": "c"})
    assert response.status_code == 400
