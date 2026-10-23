# company_client.py: a well-behaved client for company APIs. This is the code you write at every customer.
#
# It handles, so the rest of your code doesn't have to:
#   - OAuth2 client credentials: get a token, reuse it, get a new one shortly before it expires
#   - retries with exponential backoff + jitter for 429 (too many requests), 5xx errors and network blips
#   - Retry-After: when the server says "wait 1 second", wait 1 second
#   - pagination: both cursor style (CRM) and page-number style (HelpDesk)
#   - safe retries of writes with an Idempotency-Key
import random
import time
import uuid

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}     # worth trying again; 400/401/403/404 are not (they won't fix themselves)


class APIError(Exception):
    pass


class CompanyClient:
    def __init__(self, base_url, client_id, client_secret, scope="", http=None, max_retries=5,
                 backoff=0.5, timeout=10, sleep=time.sleep, clock=time.time, log=print):
        self.client_id, self.client_secret, self.scope = client_id, client_secret, scope
        self.http = http or httpx.Client(base_url=base_url, timeout=timeout)   # timeout: never wait forever
        self.max_retries, self.backoff = max_retries, backoff
        self.sleep, self.clock, self.log = sleep, clock, log                  # swappable for tests
        self._token, self._expires_at = None, 0.0
        self.stats = {"requests": 0, "retries": 0, "tokens": 0}

    # ---------- OAuth2 client credentials ----------

    def token(self):
        """Return a valid access token, fetching a new one if we have none or it expires within 30 seconds."""
        if self._token and self.clock() < self._expires_at - 30:
            return self._token
        response = self.http.post("/oauth/token", data={"grant_type": "client_credentials", "scope": self.scope},
                                  auth=(self.client_id, self.client_secret))    # HTTP Basic auth with id + secret
        if response.status_code != 200:
            raise APIError(f"token request failed: {response.status_code} {response.text}")
        body = response.json()
        self._token, self._expires_at = body["access_token"], self.clock() + body["expires_in"]
        self.stats["tokens"] += 1
        self.log(f"[auth] new token, scope='{body['scope']}', valid {body['expires_in']} s")
        return self._token

    # ---------- one request, with retries ----------

    def request(self, method, path, retry_writes=False, **kwargs):
        """Send a request and return the JSON body. GETs are retried; writes only if retry_writes=True."""
        can_retry = method == "GET" or retry_writes
        refreshed = False
        for attempt in range(self.max_retries + 1):
            headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {self.token()}"}
            kwargs["headers"] = headers
            self.stats["requests"] += 1
            try:
                response = self.http.request(method, path, **kwargs)
            except httpx.TransportError as error:                 # connection refused, timeout, DNS...
                if not can_retry or attempt == self.max_retries:
                    raise APIError(f"{method} {path}: network error {error!r}") from error
                self._wait(attempt, None, f"network error {type(error).__name__}")
                continue
            if response.status_code == 401 and not refreshed:     # token revoked or expired early: get a new one
                self._token, refreshed = None, True
                continue
            if response.status_code in RETRY_STATUS and can_retry and attempt < self.max_retries:
                self._wait(attempt, response.headers.get("Retry-After"), f"HTTP {response.status_code}")
                continue
            if response.status_code >= 400:
                raise APIError(f"{method} {path}: HTTP {response.status_code} {response.text}")
            return response.json()
        raise APIError(f"{method} {path}: still failing after {self.max_retries} retries")

    def _wait(self, attempt, retry_after, reason):
        """Exponential backoff: 0.5 s, 1 s, 2 s, 4 s... plus a random 'jitter' so many clients don't retry in sync."""
        if retry_after is not None:
            delay = float(retry_after)                           # the server told us exactly how long
        else:
            delay = self.backoff * (2 ** attempt) + random.uniform(0, self.backoff)
        self.stats["retries"] += 1
        self.log(f"[retry] {reason}, waiting {delay:.2f} s (attempt {attempt + 1} of {self.max_retries})")
        self.sleep(delay)

    # ---------- pagination ----------

    def iter_accounts(self, page_size=20):
        """CRM, cursor style: keep asking with the cursor until the server says there is no next page."""
        cursor = None
        while True:
            params = {"limit": page_size, **({"cursor": cursor} if cursor else {})}
            body = self.request("GET", "/crm/accounts", params=params)
            yield from body["data"]                             # hand out accounts one by one
            cursor = body["next_cursor"]
            if not cursor:
                return

    def iter_tickets(self, status=None, per_page=25):
        """HelpDesk, page-number style: ask page 1, 2, 3... until we have 'total' tickets."""
        page = 1
        while True:
            params = {"page": page, "per_page": per_page, **({"status": status} if status else {})}
            body = self.request("GET", "/helpdesk/tickets", params=params)
            yield from body["tickets"]
            if page * body["per_page"] >= body["total"] or not body["tickets"]:
                return
            page += 1

    # ---------- writes ----------

    def add_note(self, ticket_id, text, idempotency_key=None):
        """Add an internal note. The Idempotency-Key makes retrying safe: the server adds the note at most once."""
        key = idempotency_key or str(uuid.uuid4())
        return self.request("POST", f"/helpdesk/tickets/{ticket_id}/notes", retry_writes=True,
                            json={"body": text}, headers={"Idempotency-Key": key})
