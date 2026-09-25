"""Fixtures for template generation tests."""
from __future__ import annotations

from pathlib import Path

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
    "python_version": "3.11",
    "databricks_runtime": "15.4",
    "cloud_provider": "aws",
}


@pytest.fixture(scope="module")
def generated_project(tmp_path_factory):
    """Generate a project from the template into a temp directory."""
    import copier

    dst = tmp_path_factory.mktemp("generated")
    copier.run_copy(
        src_path=str(TEMPLATE_ROOT),
        dst_path=str(dst),
        data=DEFAULT_ANSWERS,
        defaults=True,
        overwrite=True,
        unsafe=True,  # needed if _tasks is ever added to copier.yml
    )
    return dst
