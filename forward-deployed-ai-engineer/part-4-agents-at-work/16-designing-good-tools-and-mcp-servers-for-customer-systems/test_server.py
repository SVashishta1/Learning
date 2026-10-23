"""Tests (pytest -v): the MCP server is called in-process through a real MCP client; no network, no API key."""
import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp import Client

import agent_demo
import llm
import northwind_api
import server
import tool_lint
from bad_tools import BAD_TOOLS
from fake_llm import FakeClaude


def call(name, args):
    async def go():
        async with Client(server.mcp) as client:
            result = await client.call_tool(name, args)
            return result.is_error, result.content[0].text
    return asyncio.run(go())


@pytest.fixture(autouse=True)
def fresh_api():
    server._api = TestClient(northwind_api.app, headers={"X-Api-Key": northwind_api.API_KEY})
    northwind_api.IDEMPOTENCY.clear()
    for t in northwind_api.TICKETS.values():
        t["notes"].clear()
    yield


def test_tools_and_their_safety_hints():
    tools = {t["name"]: t for t in asyncio.run(tool_lint.server_tools())}
    assert set(tools) == {"find_customers", "list_shipments", "get_shipment", "search_tickets", "add_ticket_note"}
    assert all(tools[n]["annotations"]["read_only_hint"] for n in tools if n != "add_ticket_note")
    assert tools["add_ticket_note"]["annotations"]["idempotent_hint"] is True
    assert tools["list_shipments"]["input_schema"]["properties"]["status"]["enum"][0] == "any"


def test_lint_passes_good_tools_and_flags_bad_ones():
    assert all(tool_lint.lint(t) == [] for t in asyncio.run(tool_lint.server_tools()))
    assert all(len(tool_lint.lint(t)) >= 4 for t in BAD_TOOLS)


def test_find_and_paginate():
    error, text = call("find_customers", {"query": "kestrel"})
    assert not error and "C-104" in text and "C-522" in text
    error, text = call("list_shipments", {"customer_id": "C-104"})
    assert "page 1 of 2" in text and "page=2" in text
    error, text = call("list_shipments", {"customer_id": "C-104", "page": 2})
    assert "page 2 of 2" in text and "page=3" not in text


def test_summary_versus_full_detail():
    _, summary = call("get_shipment", {"shipment_id": "NW-58445"})
    _, full = call("get_shipment", {"shipment_id": "NW-58445", "detail": "full"})
    assert "Latest: delayed" in summary and full.count("\n") == 3


def test_errors_tell_the_model_what_to_do_next():
    error, text = call("get_shipment", {"shipment_id": "NW-1234"})
    assert error and "pattern" in text                              # rejected before reaching the API
    error, text = call("get_shipment", {"shipment_id": "NW-00001"})
    assert error and "list_shipments" in text
    error, text = call("list_shipments", {"customer_id": "C-999"})
    assert error and "find_customers" in text


def test_note_is_not_duplicated_on_retry():
    args = {"ticket_id": 9001, "note": "Checked the delays.", "idempotency_key": "test-key-0001"}
    assert call("add_ticket_note", args) == (False, "Added note #1 to ticket 9001.")
    error, text = call("add_ticket_note", args)
    assert "no duplicate" in text and len(northwind_api.TICKETS[9001]["notes"]) == 1


def test_wrong_api_key_gives_a_safe_config_error():
    server._api = TestClient(northwind_api.app, headers={"X-Api-Key": "wrong"})
    error, text = call("find_customers", {"query": "kestrel"})
    assert error and "administrator" in text and "wrong" not in text


def test_api_down_gives_a_retry_once_message():
    server._api = httpx.Client(base_url="http://127.0.0.1:9", timeout=1)      # nothing listens on port 9
    error, text = call("find_customers", {"query": "kestrel"})
    assert error and "not reachable" in text


def test_agent_loop_over_stdio_with_the_scripted_stand_in():
    llm.set_client(FakeClaude(responder=agent_demo.offline_responder))
    answer = asyncio.run(agent_demo.run("Which Kestrel Pharmacy shipments are delayed?"))
    assert "NW-58445" in answer and "vehicle fault" in answer
