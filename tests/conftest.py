"""Fixtures for template generation tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import copier
import pytest
from databricks_api_mock import DatabricksApiMock

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ANSWERS = {
    "project_name": "Test Spark Job",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "databricks_host": "https://test.cloud.databricks.com",
    "unity_catalog_name": "test_catalog",
    "compute": "serverless",
}

JOB_CLUSTER = {"compute": "job_cluster", "databricks_runtime": "16.4", "cloud_provider": "aws"}


def _generate(dst: Path, **overrides: Any) -> Path:
    copier.run_copy(
        src_path=str(TEMPLATE_ROOT),
        dst_path=str(dst),
        data={**DEFAULT_ANSWERS, **overrides},
        defaults=True,
        overwrite=True,
        unsafe=True,  # needed if _tasks is ever added to copier.yml
        vcs_ref="HEAD",  # latest commit (incl. dirty changes), not the most recent tag
    )
    return dst


@pytest.fixture
def make_project(tmp_path: Path) -> Callable[..., Path]:
    """Factory rendering the template with DEFAULT_ANSWERS updated by keyword overrides."""
    return lambda **overrides: _generate(tmp_path / "project", **overrides)


@pytest.fixture(scope="module", params=["serverless", "job_cluster"])
def generated_project(request, tmp_path_factory) -> Path:
    """Project rendered once per compute type."""
    overrides = JOB_CLUSTER if request.param == "job_cluster" else {}
    return _generate(tmp_path_factory.mktemp(request.param), **overrides)


@pytest.fixture(scope="session")
def databricks_api() -> Iterator[str]:
    """Base URL of a fake Databricks API."""
    with DatabricksApiMock() as url:
        yield url
