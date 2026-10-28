"""northwind_client.py: the ONE place that talks to Northwind's systems (mock or real).

Gets an OAuth token, adds it to every request, retries busy (503/429) answers with growing waits,
and turns errors into plain messages an agent can understand.
MOCK_API_URL not set -> runs the mock in-process (handy for the CLI and tests); compose sets it to http://mock-api:8100.
"""
import os
import time

import httpx


class NorthwindClient:
    def __init__(self, base_url: str | None = None, http: httpx.Client | None = None):
        base_url = base_url if base_url is not None else os.getenv("MOCK_API_URL", "")
        if http is None and not base_url:
            from fastapi.testclient import TestClient      # an httpx.Client that calls the app directly, no network
            import mock_api
            http, base_url = TestClient(mock_api.app), "http://testserver"
        self.base = base_url.rstrip("/")
        self.http = http or httpx.Client(timeout=10)
        self.client_id = os.getenv("MOCK_CLIENT_ID", "claims-desk")
        self.client_secret = os.getenv("MOCK_CLIENT_SECRET", "claims-desk-secret-change-me")
        self._token, self._expires = "", 0.0

    def _auth(self) -> dict:
        if time.time() > self._expires - 30:                  # renew 30 s before it expires
            r = self.http.post(f"{self.base}/oauth/token", data={"client_id": self.client_id,
                               "client_secret": self.client_secret, "grant_type": "client_credentials"})
            r.raise_for_status()
            self._token, self._expires = r.json()["access_token"], time.time() + r.json()["expires_in"]
        return {"Authorization": f"Bearer {self._token}"}

    def request(self, method: str, path: str, **kw):
        for attempt in range(5):
            r = self.http.request(method, f"{self.base}{path}", headers=self._auth(), **kw)
            if r.status_code in (429, 503) and attempt < 4:
                time.sleep(0.1 * 2 ** attempt)               # wait 0.1, 0.2, 0.4, 0.8 s ("exponential backoff")
                continue
            if r.status_code == 404:
                raise KeyError(r.json().get("detail", "not found"))
            r.raise_for_status()
            return r.json()

    def shipment(self, tracking: str) -> dict:
        return self.request("GET", f"/tms/shipments/{tracking}")

    def new_claims(self) -> list[dict]:
        return self.request("GET", "/helpdesk/tickets", params={"queue": "claims", "status": "new"})

    def ticket(self, ticket_id: str) -> dict:
        return self.request("GET", f"/helpdesk/tickets/{ticket_id}")

    def add_note(self, ticket_id: str, text: str) -> dict:
        return self.request("POST", f"/helpdesk/tickets/{ticket_id}/notes", json={"text": text})

    def send_reply(self, ticket_id: str, text: str) -> dict:
        return self.request("POST", f"/helpdesk/tickets/{ticket_id}/replies", json={"text": text})

    def issue_credit(self, ticket_id: str, tracking: str, amount: float, approved_by: str) -> dict:
        return self.request("POST", "/finance/credits", json={"ticket_id": ticket_id, "tracking": tracking,
                                                              "amount_eur": amount, "approved_by": approved_by})
