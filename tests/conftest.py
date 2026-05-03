"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dataiku_codex_mcp.client import DataikuDSSAdapter
from dataiku_codex_mcp.config import AppSettings, OperationMode


class FakeDataset:
    """Fake dataset handle."""

    def __init__(
        self,
        name: str,
        dataset_type: str,
        connection: str,
        columns: list[dict[str, object]],
    ) -> None:
        self.name = name
        self.dataset_type = dataset_type
        self.connection = connection
        self.columns = columns

    def get_schema(self) -> dict[str, object]:
        return {"columns": self.columns}


class FakeRecipe:
    """Fake recipe handle."""

    def __init__(
        self,
        name: str,
        recipe_type: str,
        inputs: list[str],
        outputs: list[str],
        code: str,
        code_env_name: str | None = None,
    ) -> None:
        self.name = name
        self.recipe_type = recipe_type
        self.inputs = inputs
        self.outputs = outputs
        self.code = code
        self.code_env_name = code_env_name

    def get_definition(self) -> dict[str, object]:
        return {
            "name": self.name,
            "type": self.recipe_type,
            "inputs": [{"ref": value} for value in self.inputs],
            "outputs": [{"ref": value} for value in self.outputs],
        }

    def get_settings(self) -> FakeRecipeSettings:
        return FakeRecipeSettings(self)

    def get_code(self) -> str:
        return self.code


class FakeRecipeSettings:
    """Fake mutable recipe settings."""

    def __init__(self, recipe: FakeRecipe) -> None:
        self._recipe = recipe
        self.engine = recipe.recipe_type
        self.tags = ["critical"]
        self.code_env_name = recipe.code_env_name

    def get_code(self) -> str:
        return self._recipe.code

    def set_code(self, new_code: str) -> None:
        self._recipe.code = new_code

    def save(self) -> None:
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "tags": list(self.tags),
            "code_env_name": self.code_env_name,
        }


class FakeManagedFolder:
    """Fake Managed Folder handle."""

    def __init__(
        self,
        folder_id: str,
        name: str,
        backend_type: str,
        connection: str,
        partitioning: str,
        local_path_available: bool,
        files: list[dict[str, object]],
    ) -> None:
        self.folder_id = folder_id
        self.name = name
        self.backend_type = backend_type
        self.connection = connection
        self.partitioning = partitioning
        self.local_path_available = local_path_available
        self.files = files

    def get_info(self) -> dict[str, object]:
        return {
            "folderId": self.folder_id,
            "name": self.name,
            "backendType": self.backend_type,
            "connection": self.connection,
            "partitioning": self.partitioning,
            "localPathAvailable": self.local_path_available,
        }

    def list_files(
        self,
        *,
        path: str = "/",
        recursive: bool = False,
    ) -> list[dict[str, object]]:
        del path
        del recursive
        return list(self.files)

    def put_file(self, path: str, file_like: object) -> dict[str, object]:
        if hasattr(file_like, "read"):
            content = file_like.read()
        else:
            content = file_like
        if isinstance(content, str):
            payload = content.encode("utf-8")
        else:
            payload = bytes(content)
        normalized_path = path.lstrip("/")
        for file_entry in self.files:
            if file_entry.get("path") == normalized_path:
                file_entry["size"] = len(payload)
                file_entry["lastModified"] = "2026-05-02T12:00:00Z"
                return dict(file_entry)
        new_entry = {
            "path": normalized_path,
            "size": len(payload),
            "lastModified": "2026-05-02T12:00:00Z",
        }
        self.files.append(new_entry)
        return dict(new_entry)


class FakeCodeEnv:
    """Fake Dataiku code environment handle."""

    def __init__(
        self,
        name: str,
        python_version: str,
        packages: list[str],
        known_issues: list[str],
    ) -> None:
        self.name = name
        self.python_version = python_version
        self.packages = packages
        self.known_issues = known_issues

    def get_definition(self) -> dict[str, object]:
        return {
            "name": self.name,
            "language": "python",
            "pythonVersion": self.python_version,
            "packages": self.packages,
            "known_issues": self.known_issues,
        }


class FakeScenarioSettings:
    """Fake scenario settings object."""

    def __init__(self, scenario: FakeScenario) -> None:
        self._scenario = scenario
        self.name = scenario.name
        self.active = scenario._active
        self.code = scenario.code
        self.raw_triggers = [{"type": scenario._trigger_type}] if scenario._trigger_type else []
        self.data = {
            "name": self.name,
            "active": self.active,
            "type": scenario.scenario_type,
            "triggers": self.raw_triggers,
            "params": {"steps": list(scenario.steps)},
        }

    def get_raw(self) -> dict[str, object]:
        return dict(self.data)

    def save(self) -> None:
        self._scenario.name = self.name
        self._scenario._active = self.active
        self._scenario.code = self.code
        raw_params = self.data.get("params", {})
        raw_steps = raw_params.get("steps", []) if isinstance(raw_params, dict) else []
        self._scenario.steps = list(raw_steps) if isinstance(raw_steps, list) else []


class FakeScenarioStatus:
    """Fake scenario status object."""

    def __init__(self, *, running: bool, active: bool) -> None:
        self.running = running
        self.data = {"running": running, "active": active}

    def get_raw(self) -> dict[str, object]:
        return dict(self.data)


class FakeScenarioRun:
    """Fake scenario run handle."""

    def __init__(
        self,
        *,
        project_key: str,
        scenario_id: str,
        run_id: str,
        outcome: str,
        log_text: str,
        start_time: datetime,
        duration_seconds: int,
        step_runs: list[dict[str, object]],
    ) -> None:
        self.project_key = project_key
        self.scenario_id = scenario_id
        self.id = run_id
        self._outcome = outcome
        self._log_text = log_text
        self.start_time = start_time
        self.duration = duration_seconds
        self._step_runs = step_runs
        self.run = {
            "runId": run_id,
            "scenario": {"projectKey": project_key, "id": scenario_id},
            "start": int(start_time.timestamp() * 1000),
            "end": int((start_time + timedelta(seconds=duration_seconds)).timestamp() * 1000),
            "result": {"outcome": outcome},
        }

    @property
    def outcome(self) -> str:
        return self._outcome

    @property
    def running(self) -> bool:
        return False

    def get_info(self) -> dict[str, object]:
        return dict(self.run)

    def get_details(self) -> dict[str, object]:
        first_error: dict[str, object] | None = None
        for step in self._step_runs:
            result = step.get("result")
            if isinstance(result, dict) and isinstance(result.get("thrown"), dict):
                first_error = result["thrown"]
                break
        payload: dict[str, object] = {
            "scenarioRun": self.get_info(),
            "stepRuns": list(self._step_runs),
        }
        if first_error is not None:
            payload["first_error_details"] = first_error
        return payload

    def get_log(self, step_id: str | None = None) -> str:
        del step_id
        return self._log_text


class FakeTriggerFire:
    """Fake trigger fire returned by scenario.run()."""

    def __init__(self, scenario: FakeScenario, scenario_run: FakeScenarioRun) -> None:
        self.scenario = scenario
        self.trigger_id = f"manual-{scenario.id}"
        self.run_id = f"trigger-{scenario_run.id}"
        self._scenario_run = scenario_run
        self.trigger_fire = {
            "trigger": {"id": self.trigger_id},
            "runId": self.run_id,
            "cancelled": False,
        }

    def get_raw(self) -> dict[str, object]:
        return dict(self.trigger_fire)

    def get_scenario_run(self) -> FakeScenarioRun:
        return self._scenario_run


class FakeScenario:
    """Fake scenario handle."""

    def __init__(
        self,
        *,
        project_key: str,
        scenario_id: str,
        name: str,
        active: bool,
        running: bool,
        trigger_type: str,
        runs: list[FakeScenarioRun],
        scenario_type: str = "step_based",
        code: str = "",
        steps: list[dict[str, object]] | None = None,
    ) -> None:
        self.project_key = project_key
        self.id = scenario_id
        self.name = name
        self._active = active
        self._running = running
        self._trigger_type = trigger_type
        self.scenario_type = scenario_type
        self.code = code
        self.steps = list(steps or [])
        self._runs = {run.id: run for run in runs}
        self._ordered_run_ids = [run.id for run in runs]

    def get_settings(self) -> FakeScenarioSettings:
        return FakeScenarioSettings(self)

    def get_status(self) -> FakeScenarioStatus:
        return FakeScenarioStatus(running=self._running, active=self._active)

    def get_last_runs(
        self,
        limit: int = 10,
        only_finished_runs: bool = False,
    ) -> list[FakeScenarioRun]:
        del only_finished_runs
        return [self._runs[run_id] for run_id in self._ordered_run_ids[:limit]]

    def get_run(self, run_id: str) -> FakeScenarioRun:
        if run_id not in self._runs:
            raise ValueError(f"Run not found: {run_id}")
        return self._runs[run_id]

    def run(self, params: dict[str, object] | None = None) -> FakeTriggerFire:
        del params
        if not self._ordered_run_ids:
            created_run = FakeScenarioRun(
                project_key=self.project_key,
                scenario_id=self.id,
                run_id=f"run_{self.id}_001",
                outcome="SUCCESS",
                log_text="INFO scenario completed\n",
                start_time=datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc),
                duration_seconds=5,
                step_runs=[],
            )
            self._runs[created_run.id] = created_run
            self._ordered_run_ids.insert(0, created_run.id)
        latest_run = self._runs[self._ordered_run_ids[0]]
        return FakeTriggerFire(self, latest_run)


class FakeJob:
    """Fake DSS job handle."""

    def __init__(
        self,
        *,
        job_id: str,
        log_text: str,
        status: dict[str, object],
    ) -> None:
        self.id = job_id
        self._log_text = log_text
        self._status = status

    def get_log(self, activity: str | None = None) -> str:
        del activity
        return self._log_text

    def get_status(self) -> dict[str, object]:
        return dict(self._status)


class FakeLibraryFile:
    """Fake project library file."""

    def __init__(self, path: str, initial_content: str = "") -> None:
        self.path = path
        self.content = initial_content

    def write(self, data: str) -> None:
        self.content = data


class FakeLibrary:
    """Fake project library."""

    def __init__(self) -> None:
        self.files: dict[str, FakeLibraryFile] = {}

    def get_file(self, path: str) -> FakeLibraryFile | None:
        return self.files.get(path.lstrip("/"))

    def add_file(self, file_name: str) -> FakeLibraryFile:
        normalized = file_name.lstrip("/")
        file_handle = FakeLibraryFile(normalized)
        self.files[normalized] = file_handle
        return file_handle


class FakeWikiArticleData:
    """Fake wiki article data."""

    def __init__(self, article: FakeWikiArticle) -> None:
        self.article = article

    def set_body(self, content: str) -> None:
        self.article.body = content

    def save(self) -> None:
        return None


class FakeWikiArticle:
    """Fake wiki article."""

    def __init__(self, name: str, body: str = "") -> None:
        self.article_id = name
        self.name = name
        self.body = body

    def get_data(self) -> FakeWikiArticleData:
        return FakeWikiArticleData(self)


class FakeWiki:
    """Fake project wiki."""

    def __init__(self) -> None:
        self.articles: dict[str, FakeWikiArticle] = {}

    def get_article(self, article_id_or_name: str) -> FakeWikiArticle:
        if article_id_or_name not in self.articles:
            raise ValueError(f"Article not found: {article_id_or_name}")
        return self.articles[article_id_or_name]

    def create_article(
        self,
        article_name: str,
        parent_id: str | None = None,
        content: str | None = None,
    ) -> FakeWikiArticle:
        del parent_id
        article = FakeWikiArticle(article_name, content or "")
        self.articles[article_name] = article
        return article


class FakeRecipeCreator:
    """Fake recipe creator for project.new_recipe()."""

    def __init__(self, project: FakeProject, recipe_type: str, name: str) -> None:
        self.project = project
        self.recipe_type = recipe_type
        self.name = name
        self.inputs: list[str] = []
        self.outputs: list[str] = []

    def with_input(
        self,
        input_id: str,
        project_key: str | None = None,
        role: str = "main",
    ) -> FakeRecipeCreator:
        del project_key
        del role
        self.inputs.append(input_id)
        return self

    def with_output(
        self,
        output_id: str,
        append: bool = False,
        role: str = "main",
    ) -> FakeRecipeCreator:
        del append
        del role
        self.outputs.append(output_id)
        return self

    def create(self) -> FakeRecipe:
        recipe = FakeRecipe(
            self.name,
            self.recipe_type,
            list(self.inputs),
            list(self.outputs),
            "",
        )
        self.project.recipes[self.name] = recipe
        return recipe


class FakeProject:
    """Fake project handle."""

    def __init__(self, project_key: str, name: str) -> None:
        self.project_key = project_key
        self.name = name
        self.datasets = {
            "orders": FakeDataset(
                "orders",
                "SQL",
                "warehouse",
                [
                    {"name": "order_id", "type": "bigint"},
                    {"name": "customer_email", "type": "string"},
                ],
            ),
            "chunks": FakeDataset(
                "chunks",
                "Filesystem",
                "filesystem_default",
                [
                    {"name": "chunk_id", "type": "string"},
                    {"name": "content", "type": "string"},
                    {"name": "source_path", "type": "string"},
                ],
            ),
        }
        self.recipes = {
            "build_chunks": FakeRecipe(
                "build_chunks",
                "python",
                ["orders"],
                ["chunks"],
                (
                    "import dataiku\n"
                    "from langchain.text_splitter import RecursiveCharacterTextSplitter\n"
                    "from sentence_transformers import SentenceTransformer\n"
                    "import faiss\n\n"
                    "folder = dataiku.Folder('RAW_DOCS')\n"
                    "path = folder.get_path()\n"
                    "with open(path + '/doc1.jsonl', 'r', encoding='utf-8') as stream:\n"
                    "    payload = stream.read()\n\n"
                    "api_key=super-secret\n"
                    "splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=0)\n"
                    "model = SentenceTransformer('all-MiniLM-L6-v2')\n"
                    "index = faiss.IndexFlatIP(1536)\n"
                    "top_k = 50\n"
                    "chunks = splitter.split_text(payload)\n"
                    "embeddings = model.encode(chunks)\n"
                ),
                code_env_name="rag-env",
            ),
            "join_orders": FakeRecipe(
                "join_orders",
                "sql",
                ["orders", "chunks"],
                ["enriched_orders"],
                "SELECT * FROM orders",
            ),
        }
        self.managed_folders = {
            "RAW_DOCS": FakeManagedFolder(
                "RAW_DOCS",
                "Raw Documents",
                "S3",
                "s3_docs",
                "NONE",
                False,
                [
                    {
                        "path": "doc1.jsonl",
                        "size": 123,
                        "lastModified": "2026-05-01T09:00:00Z",
                    },
                    {
                        "path": "doc2.jsonl",
                        "size": 456,
                        "lastModified": "2026-05-01T10:00:00Z",
                    },
                ],
            )
        }
        scenario_start = datetime(2026, 5, 1, 8, 30, tzinfo=timezone.utc)
        self.scenario_handles = {
            "daily_refresh": FakeScenario(
                project_key=project_key,
                scenario_id="daily_refresh",
                name="Daily Refresh",
                active=True,
                running=False,
                trigger_type="daily",
                runs=[
                    FakeScenarioRun(
                        project_key=project_key,
                        scenario_id="daily_refresh",
                        run_id="run_daily_001",
                        outcome="SUCCESS",
                        log_text=(
                            "INFO scenario started\n"
                            "INFO build_orders completed successfully\n"
                            "INFO scenario completed\n"
                        ),
                        start_time=scenario_start,
                        duration_seconds=120,
                        step_runs=[
                            {
                                "stepName": "build_orders",
                                "result": {"outcome": "SUCCESS"},
                                "additionalReportItems": [],
                            }
                        ],
                    )
                ],
            ),
            "backfill_rag": FakeScenario(
                project_key=project_key,
                scenario_id="backfill_rag",
                name="Backfill RAG",
                active=False,
                running=False,
                trigger_type="manual",
                runs=[
                    FakeScenarioRun(
                        project_key=project_key,
                        scenario_id="backfill_rag",
                        run_id="run_backfill_001",
                        outcome="FAILED",
                        log_text=(
                            "INFO start backfill\n"
                            "ERROR ImportError: No module named sentence_transformers\n"
                            "ERROR code env rag-env is missing package sentence-transformers\n"
                            "api_key=run-secret-token\n"
                        ),
                        start_time=scenario_start + timedelta(hours=2),
                        duration_seconds=45,
                        step_runs=[
                            {
                                "stepName": "embed_documents",
                                "result": {
                                    "outcome": "FAILED",
                                    "thrown": {
                                        "title": "ImportError",
                                        "message": "No module named sentence_transformers",
                                        "clazz": "ImportError",
                                        "code": "ERR_PYTHON_IMPORT",
                                    },
                                },
                                "additionalReportItems": [],
                            }
                        ],
                    )
                ],
            ),
        }
        self.jobs = {
            "job_build_embeddings": FakeJob(
                job_id="job_build_embeddings",
                log_text=(
                    "INFO building embeddings\n"
                    "ERROR ImportError: No module named sentence_transformers\n"
                    "ERROR Authorization: Bearer job-secret-token\n"
                    "ERROR code env rag-env failed to resolve dependencies\n"
                    "ERROR stack trace line\n"
                ),
                status={
                    "baseStatus": "FAILED",
                    "activities": [
                        {"name": "embed_documents", "state": "FAILED"},
                    ],
                    "errorDetails": {
                        "title": "ImportError",
                        "message": "No module named sentence_transformers",
                        "clazz": "ImportError",
                    },
                },
            )
        }
        self.library = FakeLibrary()
        self.wiki = FakeWiki()

    def get_summary(self) -> dict[str, object]:
        return {"projectKey": self.project_key, "name": self.name}

    def list_datasets(self) -> list[dict[str, object]]:
        return [
            {
                "name": dataset.name,
                "type": dataset.dataset_type,
                "connection": dataset.connection,
                "schemaColumnsCount": len(dataset.columns),
                "tags": ["gold"] if dataset.name == "orders" else ["rag"],
            }
            for dataset in self.datasets.values()
        ]

    def get_dataset(self, dataset_name: str) -> FakeDataset:
        return self.datasets[dataset_name]

    def list_recipes(self) -> list[dict[str, object]]:
        return [
            {
                "name": recipe.name,
                "type": recipe.recipe_type,
                "inputs": [{"ref": value} for value in recipe.inputs],
                "outputs": [{"ref": value} for value in recipe.outputs],
                "lastModifiedOn": "2026-05-01T12:00:00Z",
            }
            for recipe in self.recipes.values()
        ]

    def get_recipe(self, recipe_name: str) -> FakeRecipe:
        return self.recipes[recipe_name]

    def new_recipe(self, recipe_type: str, name: str | None = None) -> FakeRecipeCreator:
        return FakeRecipeCreator(self, recipe_type, name or f"{recipe_type}_recipe")

    def list_managed_folders(self) -> list[dict[str, object]]:
        return [
            {
                "folderId": folder.folder_id,
                "name": folder.name,
                "type": folder.backend_type,
                "connection": folder.connection,
                "partitioning": folder.partitioning,
            }
            for folder in self.managed_folders.values()
        ]

    def get_managed_folder(self, folder_id: str) -> FakeManagedFolder:
        return self.managed_folders[folder_id]

    def create_managed_folder(
        self,
        name: str,
        folder_type: str | None = None,
        connection_name: str = "filesystem_folders",
    ) -> FakeManagedFolder:
        folder = FakeManagedFolder(
            name,
            name,
            folder_type or "Filesystem",
            connection_name,
            "NONE",
            True,
            [],
        )
        self.managed_folders[name] = folder
        return folder

    def create_scenario(
        self,
        scenario_name: str,
        scenario_type: str,
        definition: dict[str, object] | None = None,
    ) -> FakeScenario:
        resolved_definition = definition or {"params": {}}
        raw_triggers = resolved_definition.get("triggers", [])
        trigger_type = "manual"
        if isinstance(raw_triggers, list) and raw_triggers:
            first_trigger = raw_triggers[0]
            if isinstance(first_trigger, dict):
                trigger_type = str(first_trigger.get("type") or trigger_type)
        raw_params = resolved_definition.get("params", {})
        raw_steps = raw_params.get("steps", []) if isinstance(raw_params, dict) else []
        scenario = FakeScenario(
            project_key=self.project_key,
            scenario_id=scenario_name,
            name=scenario_name,
            active=bool(resolved_definition.get("active", False)),
            running=False,
            trigger_type=trigger_type,
            runs=[],
            scenario_type=scenario_type,
            code="",
            steps=list(raw_steps) if isinstance(raw_steps, list) else [],
        )
        self.scenario_handles[scenario_name] = scenario
        return scenario

    def list_scenarios(self, as_type: str = "listitems") -> list[object]:
        if as_type == "objects":
            return list(self.scenario_handles.values())
        return [
            {
                "scenarioId": scenario.id,
                "name": scenario.name,
                "active": scenario.get_settings().active,
                "running": scenario.get_status().running,
            }
            for scenario in self.scenario_handles.values()
        ]

    def get_scenario(self, scenario_id: str) -> FakeScenario:
        return self.scenario_handles[scenario_id]

    def get_job(self, job_id: str) -> FakeJob:
        return self.jobs[job_id]

    def get_library(self) -> FakeLibrary:
        return self.library

    def get_wiki(self) -> FakeWiki:
        return self.wiki


class FakeDataikuClient:
    """Small fake client used across tests."""

    def __init__(self) -> None:
        self.projects = [
            {"projectKey": "A", "name": "Alpha", "owner": "alice", "tags": ["prod"]},
            {
                "projectKey": "ARCHIVE",
                "name": "Archive",
                "owner": "bob",
                "status": "archived",
            },
        ]
        self.project_handles = {"A": FakeProject("A", "Alpha")}
        self.code_envs = {
            "rag-env": FakeCodeEnv(
                "rag-env",
                "3.9",
                ["langchain==0.2.1", "faiss-cpu==1.7.4", "pandas==2.2.2"],
                ["Offline wheel for sentence-transformers is missing."],
            )
        }

    def get_info(self) -> dict[str, object]:
        return {"version": "14.0.2", "user": "tester", "features": ["projects"]}

    def list_projects(self) -> list[dict[str, object]]:
        return list(self.projects)

    def get_project(self, project_key: str) -> FakeProject:
        return self.project_handles[project_key]

    def list_code_envs(self) -> list[dict[str, object]]:
        return [
            {
                "name": code_env.name,
                "language": "python",
                "pythonVersion": code_env.python_version,
                "packagesCount": len(code_env.packages),
            }
            for code_env in self.code_envs.values()
        ]

    def get_code_env(self, env_lang: str | None, env_name: str | None = None) -> FakeCodeEnv:
        resolved_name = env_name if env_name is not None else env_lang
        assert resolved_name is not None
        return self.code_envs[resolved_name]


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        dss_url="https://dss.example.com",
        api_key="secret-key",  # type: ignore[arg-type]
        mode=OperationMode.READONLY,
    )


@pytest.fixture
def fake_client() -> FakeDataikuClient:
    return FakeDataikuClient()


@pytest.fixture
def adapter(settings: AppSettings, fake_client: FakeDataikuClient) -> DataikuDSSAdapter:
    return DataikuDSSAdapter(settings, client=fake_client)
