"""Fixtures for template generation tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import copier
import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ANSWERS = {
    "project_name": "Test Spark Job",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "databricks_host": "https://test.cloud.databricks.com",
    "unity_catalog_name": "test_catalog",
    "databricks_runtime": "15.4",
    "cloud_provider": "aws",
}


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


@pytest.fixture(scope="module")
def generated_project(tmp_path_factory) -> Path:
    """Project rendered once with the default answers."""
    return _generate(tmp_path_factory.mktemp("generated"))
