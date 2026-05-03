from __future__ import annotations

from dataiku_codex_mcp.client import DataikuClientFactory


def test_ping_returns_normalized_instance_data(adapter: object) -> None:
    payload = adapter.ping()

    assert payload["reachable"] is True
    assert payload["version"] == "14.0.2"
    assert payload["user"] == "tester"


def test_list_projects_filters_archived_projects(adapter: object) -> None:
    projects = adapter.list_projects()

    assert len(projects) == 1
    assert projects[0]["project_key"] == "A"


def test_list_projects_can_include_archived_projects(adapter: object) -> None:
    projects = adapter.list_projects(include_archived=True)

    assert {project["project_key"] for project in projects} == {"A", "ARCHIVE"}


def test_get_project_summary_returns_object_counts(adapter: object) -> None:
    summary = adapter.get_project_summary("A")

    assert summary["datasets_count"] == 2
    assert summary["recipes_count"] == 2
    assert summary["managed_folders_count"] == 1
    assert summary["scenarios_count"] == 2


def test_get_dataset_schema_returns_columns(adapter: object) -> None:
    schema = adapter.get_dataset_schema("A", "chunks")

    assert [column["name"] for column in schema["columns"]] == [
        "chunk_id",
        "content",
        "source_path",
    ]


def test_get_recipe_details_returns_code(adapter: object) -> None:
    recipe = adapter.get_recipe_details("A", "build_chunks")

    assert recipe["name"] == "build_chunks"
    assert recipe["type"] == "python"
    assert "api_key=super-secret" in recipe["code"]


def test_get_managed_folder_info_reports_non_local_backend(adapter: object) -> None:
    info = adapter.get_managed_folder_info("A", "RAW_DOCS")

    assert info["backend_type"] == "S3"
    assert info["local_path_available"] is False
    assert info["warnings"]


def test_list_folder_files_can_truncate(adapter: object) -> None:
    listing = adapter.list_folder_files("A", "RAW_DOCS", limit=1)

    assert listing["truncated"] is True
    assert len(listing["files"]) == 1


def test_client_factory_creates_dataiku_client(settings: object) -> None:
    factory = DataikuClientFactory(settings)
    client = factory.create()

    assert client is not None
