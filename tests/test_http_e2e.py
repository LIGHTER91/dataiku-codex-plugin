from __future__ import annotations

import asyncio
import json
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from fastmcp.utilities.tests import run_server_async

from dataiku_codex_mcp.config import AppSettings, OperationMode, RemoteAuthMode
from dataiku_codex_mcp.server import build_app_context, create_mcp_server


def _extract_payload(result: Any) -> dict[str, Any]:
    if isinstance(result.data, dict):
        return result.data
    if isinstance(result.structured_content, dict):
        return result.structured_content
    for block in result.content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return json.loads(text)
    raise AssertionError("Could not extract a structured payload from the tool result.")


def _bearer_http_settings(**overrides: object) -> AppSettings:
    payload: dict[str, object] = {
        "dss_url": "https://dss.example.com",
        "api_key": "secret-key",
        "mode": OperationMode.READONLY,
        "remote_auth_mode": RemoteAuthMode.BEARER,
        "bearer_tokens_json": [
            {
                "token": "local-http-token",
                "subject": "alice@example.com",
                "client_id": "alice-cli",
                "roles": ["reader", "writer", "operator"],
                "teams": ["data-platform"],
                "scopes": ["mcp:read", "mcp:write", "mcp:execute"],
            }
        ],
    }
    payload.update(overrides)
    return AppSettings(**payload)  # type: ignore[arg-type]


def test_http_e2e_bearer_ping(adapter: object) -> None:
    async def scenario() -> None:
        settings = _bearer_http_settings()
        server = create_mcp_server(build_app_context(settings=settings, dataiku=adapter))

        async with run_server_async(server, transport="http", path="/mcp") as url:
            transport = StreamableHttpTransport(url, auth="local-http-token")
            async with Client(transport) as client:
                result = await client.call_tool("dataiku_ping", {})
                payload = _extract_payload(result)

        assert payload["ok"] is True
        assert payload["data"]["reachable"] is True

    asyncio.run(scenario())


def test_http_e2e_bearer_project_summary(adapter: object) -> None:
    async def scenario() -> None:
        settings = _bearer_http_settings()
        server = create_mcp_server(build_app_context(settings=settings, dataiku=adapter))

        async with run_server_async(server, transport="http", path="/mcp") as url:
            transport = StreamableHttpTransport(url, auth="local-http-token")
            async with Client(transport) as client:
                result = await client.call_tool(
                    "dataiku_get_project_summary",
                    {"project_key": "A"},
                )
                payload = _extract_payload(result)

        assert payload["ok"] is True
        assert payload["data"]["project_key"] == "A"
        assert payload["data"]["datasets_count"] == 2

    asyncio.run(scenario())


def test_http_e2e_policy_denies_run_scenario(adapter: object) -> None:
    async def scenario() -> None:
        settings = _bearer_http_settings(
            mode=OperationMode.EXECUTE,
            enable_execute_tools=True,
            bearer_tokens_json=[
                {
                    "token": "reader-token",
                    "subject": "bob@example.com",
                    "client_id": "bob-cli",
                    "roles": ["reader"],
                    "teams": ["data-platform"],
                    "scopes": ["mcp:execute"],
                }
            ],
            policy_json={
                "tool_role_bindings": {"dataiku_run_scenario": ["operator"]},
                "default_decision": "allow",
            },
        )
        server = create_mcp_server(build_app_context(settings=settings, dataiku=adapter))

        async with run_server_async(server, transport="http", path="/mcp") as url:
            transport = StreamableHttpTransport(url, auth="reader-token")
            async with Client(transport) as client:
                try:
                    await client.call_tool(
                        "dataiku_run_scenario",
                        {
                            "project_key": "A",
                            "scenario_id": "nightly_embeddings",
                            "approved": True,
                            "approval_reason": "integration-test",
                        },
                    )
                except ToolError as exc:
                    assert "blocked by the configured access policy" in str(exc)
                else:
                    raise AssertionError("Expected the policy to deny the scenario execution.")

    asyncio.run(scenario())
