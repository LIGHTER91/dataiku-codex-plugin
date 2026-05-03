from __future__ import annotations

import base64
import json

import pytest

from dataiku_codex_mcp.config import OperationMode
from dataiku_codex_mcp.errors import PermissionDeniedError
from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


@pytest.fixture
def write_settings(settings: object) -> object:
    return settings.model_copy(
        update={
            "mode": OperationMode.WRITE,
            "enable_write_tools": True,
        }
    )


@pytest.fixture
def execute_settings(settings: object) -> object:
    return settings.model_copy(
        update={
            "mode": OperationMode.EXECUTE,
            "enable_execute_tools": True,
        }
    )


def test_update_recipe_code_requires_approval(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_update_recipe_code").handler(
            "A",
            "build_chunks",
            "print('changed')\n",
            "Refactor recipe",
        )

    assert exc_info.value.details["dry_run_summary"]["operation"] == "update_recipe_code"


def test_update_recipe_code_updates_recipe(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_update_recipe_code").handler(
        "A",
        "build_chunks",
        "print('changed')\n",
        "Refactor recipe",
        True,
        "User explicitly approved this action.",
    )

    assert payload["ok"] is True
    assert payload["data"]["updated"] is True
    assert adapter.get_recipe_details("A", "build_chunks")["code"] == "print('changed')\n"


def test_create_python_recipe_creates_recipe(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_create_python_recipe").handler(
        "A",
        "new_python_recipe",
        ["orders"],
        ["chunks"],
        "print('hello')\n",
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    recipe_names = {recipe["name"] for recipe in adapter.list_recipes("A")}
    assert "new_python_recipe" in recipe_names


def test_create_managed_folder_creates_folder(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_create_managed_folder").handler(
        "A",
        "EXPORTS",
        "filesystem_folders",
        None,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    folder_ids = {folder["folder_id"] for folder in adapter.list_managed_folders("A")}
    assert "EXPORTS" in folder_ids


def test_upload_file_to_folder_writes_file(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))
    content_base64 = base64.b64encode(b"hello world").decode("ascii")

    payload = registry.get("dataiku_upload_file_to_folder").handler(
        "A",
        "RAW_DOCS",
        "new_doc.txt",
        content_base64,
        False,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["uploaded"] is True
    files = adapter.list_folder_files("A", "RAW_DOCS")
    assert any(file_entry["path"] == "new_doc.txt" for file_entry in files["files"])


def test_run_scenario_requires_execute_mode(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError):
        registry.get("dataiku_run_scenario").handler(
            "A",
            "daily_refresh",
            None,
            True,
            "User explicitly approved this action.",
        )


def test_run_scenario_executes_in_execute_mode(adapter: object, execute_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=execute_settings, dataiku=adapter))

    payload = registry.get("dataiku_run_scenario").handler(
        "A",
        "daily_refresh",
        None,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["requested"] is True
    assert payload["data"]["scenario_id"] == "daily_refresh"


def test_create_project_documentation_writes_library_file(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_create_project_documentation").handler(
        "A",
        "library:docs/README.md",
        "# Project Doc\n",
        False,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["written"] is True
    fake_project = adapter.client.get_project("A")
    assert fake_project.library.get_file("docs/README.md").content == "# Project Doc\n"


def test_update_recipe_code_command_returns_dry_run_error_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    adapter: object,
    write_settings: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=write_settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "update-recipe-code",
            "A",
            "build_chunks",
            "--new-code",
            "print('x')\n",
            "--reason",
            "Refactor recipe",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["error"]["details"]["dry_run_summary"]["operation"] == "update_recipe_code"


def test_run_scenario_command_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    adapter: object,
    execute_settings: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=execute_settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "run-scenario",
            "A",
            "daily_refresh",
            "--approved",
            "--approval-reason",
            "User explicitly approved this action.",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["requested"] is True
