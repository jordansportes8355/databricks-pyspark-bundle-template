"""Tests for template generation correctness."""
from __future__ import annotations

import subprocess
from pathlib import Path


# ── File existence ────────────────────────────────────────────────────────────

EXPECTED_FILES = [
    "pyproject.toml",
    "Makefile",
    ".gitignore",
    ".pre-commit-config.yaml",
    "databricks.yml",
    "resources/test-spark-job_job.yml",
    ".github/workflows/ci.yml",
    "src/test_spark_job/__init__.py",
    "src/test_spark_job/main.py",
    "src/test_spark_job/config.py",
    "src/test_spark_job/spark.py",
    "src/test_spark_job/secrets.py",
    "src/test_spark_job/logger.py",
    "src/test_spark_job/conf/base.yaml",
    "src/test_spark_job/conf/dev.yaml",
    "src/test_spark_job/conf/staging.yaml",
    "src/test_spark_job/conf/prod.yaml",
    "src/test_spark_job/conf/logging.yaml",
    "src/test_spark_job/io/__init__.py",
    "src/test_spark_job/io/reader.py",
    "src/test_spark_job/io/writer.py",
    "src/test_spark_job/transformations/__init__.py",
    "src/test_spark_job/transformations/example.py",
    "src/test_spark_job/jobs/__init__.py",
    "src/test_spark_job/jobs/example_job.py",
    "tests/conftest.py",
    "tests/unit/__init__.py",
    "tests/unit/test_config.py",
    "tests/unit/test_example_transform.py",
    "tests/unit/test_example_job.py",
]


def test_expected_files_exist(generated_project: Path):
    missing = [f for f in EXPECTED_FILES if not (generated_project / f).exists()]
    assert not missing, f"Missing files: {missing}"


# ── Content checks ────────────────────────────────────────────────────────────

def test_pyproject_contains_project_name(generated_project: Path):
    content = (generated_project / "pyproject.toml").read_text()
    assert "Test Spark Job" in content


def test_databricks_yml_aws_node_type(generated_project: Path):
    content = (generated_project / "databricks.yml").read_text()
    assert "m5.xlarge" in content


def test_job_yml_runtime(generated_project: Path):
    content = (generated_project / "resources/test-spark-job_job.yml").read_text()
    assert "15.4" in content


def test_job_yml_email(generated_project: Path):
    content = (generated_project / "resources/test-spark-job_job.yml").read_text()
    assert "test@example.com" in content


def test_base_yaml_catalog(generated_project: Path):
    content = (generated_project / "src/test_spark_job/conf/base.yaml").read_text()
    assert "test_catalog" in content


def test_dev_yaml_catalog_suffix(generated_project: Path):
    content = (generated_project / "src/test_spark_job/conf/dev.yaml").read_text()
    assert "test_catalog_dev" in content


def test_ci_yml_no_raw_jinja(generated_project: Path):
    """GitHub Actions expressions must be preserved, not mangled by Copier."""
    content = (generated_project / ".github/workflows/ci.yml").read_text()
    assert "${{ secrets.DATABRICKS_HOST }}" in content
    assert "raw" not in content  # jinja raw tags must not leak into output


# ── Ruff lint ─────────────────────────────────────────────────────────────────

def test_ruff_passes(generated_project: Path):
    result = subprocess.run(
        ["uv", "run", "--with", "ruff", "ruff", "check", "src/", "tests/"],
        cwd=generated_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"ruff:\n{result.stdout}\n{result.stderr}"
