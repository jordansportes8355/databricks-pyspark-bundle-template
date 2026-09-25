"""Fixtures for template generation tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ANSWERS = {
    "project_name": "Test Spark Job",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "databricks_host": "https://test.cloud.databricks.com",
    "unity_catalog_name": "test_catalog",
    # computed defaults accepted as-is
    "project_slug": "test-spark-job",
    "package_name": "test_spark_job",
    "databricks_runtime": "15.4",
    "cloud_provider": "aws",
}


def generate(dst: Path, **overrides: Any) -> Path:
    """Render the template into ``dst`` with DEFAULT_ANSWERS updated by ``overrides``."""
    import copier

    copier.run_copy(
        src_path=str(TEMPLATE_ROOT),
        dst_path=str(dst),
        data={**DEFAULT_ANSWERS, **overrides},
        defaults=True,
        overwrite=True,
        unsafe=True,  # needed if _tasks is ever added to copier.yml
        vcs_ref="HEAD",  # always use latest commit, not the most recent tag
    )
    return dst


@pytest.fixture(scope="module")
def generated_project(tmp_path_factory) -> Path:
    """Generate a project from the template with the default answers."""
    return generate(tmp_path_factory.mktemp("generated"))
