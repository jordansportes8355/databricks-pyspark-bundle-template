"""Tests for template generation correctness."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from conftest import generate

# ── File existence ────────────────────────────────────────────────────────────

EXPECTED_FILES = [
    ".copier-answers.yml",
    ".env.example",
    "README.md",
    "pyproject.toml",
    "Makefile",
    ".gitignore",
    ".pre-commit-config.yaml",
    "databricks.yml",
    "resources/test_spark_job_job.yml",
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
    "tests/unit/test_io.py",
    "tests/unit/test_spark.py",
]


def test_expected_files_exist(generated_project: Path):
    missing = [f for f in EXPECTED_FILES if not (generated_project / f).exists()]
    assert not missing, f"Missing files: {missing}"


def test_no_jinja_leftovers(generated_project: Path):
    leftovers = [
        str(p) for p in generated_project.rglob("*") if p.is_file() and ("{{" in p.name or p.suffix == ".jinja")
    ]
    assert not leftovers, f"Unrendered files: {leftovers}"


# ── Content checks ────────────────────────────────────────────────────────────


def test_pyproject_contains_project_name(generated_project: Path):
    content = (generated_project / "pyproject.toml").read_text()
    assert "Test Spark Job" in content


def test_job_yml_email(generated_project: Path):
    content = (generated_project / "resources/test_spark_job_job.yml").read_text()
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


def test_answers_file_enables_copier_update(generated_project: Path):
    answers = yaml.safe_load((generated_project / ".copier-answers.yml").read_text())
    assert answers["_src_path"]
    assert answers["_commit"]
    assert answers["package_name"] == "test_spark_job"


@pytest.mark.parametrize(
    ("cloud", "node_type"),
    [("aws", "m5.xlarge"), ("azure", "Standard_DS3_v2"), ("gcp", "n2-standard-4")],
)
def test_node_type_per_cloud(tmp_path: Path, cloud: str, node_type: str):
    project = generate(tmp_path, cloud_provider=cloud)
    content = (project / "databricks.yml").read_text()
    assert f"default: {node_type}" in content


@pytest.mark.parametrize(
    ("runtime", "python", "pyspark", "scala"),
    [
        ("14.3", "3.10", "pyspark>=3.5,<3.6", "2.12"),
        ("15.4", "3.11", "pyspark>=3.5,<3.6", "2.12"),
        ("16.4", "3.12", "pyspark>=3.5,<3.6", "2.12"),
        ("17.3", "3.12", "pyspark>=4.0,<4.1", "2.13"),
    ],
)
def test_versions_follow_runtime(tmp_path: Path, runtime: str, python: str, pyspark: str, scala: str):
    project = generate(tmp_path, databricks_runtime=runtime)
    pyproject = (project / "pyproject.toml").read_text()
    job = (project / "resources/test_spark_job_job.yml").read_text()

    assert f'requires-python = ">={python}"' in pyproject
    assert f'"{pyspark}"' in pyproject
    assert f'spark_version: "{runtime}.x-scala{scala}"' in job
    assert f'python-version: "{python}"' in (project / ".github/workflows/ci.yml").read_text()


@pytest.mark.parametrize(
    "bad_answer",
    [
        {"project_slug": "Bad Slug"},
        {"package_name": "bad-package"},
        {"author_email": "not-an-email"},
        {"databricks_host": "test.cloud.databricks.com"},
        {"unity_catalog_name": "Bad-Catalog"},
    ],
)
def test_validators_reject_invalid_answers(tmp_path: Path, bad_answer: dict[str, str]):
    with pytest.raises(ValueError):
        generate(tmp_path, **bad_answer)


# ── Generated project quality gates (mirror the generated CI) ─────────────────


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def test_ruff_check_passes(generated_project: Path):
    result = _run(["uvx", "ruff", "check", "src/", "tests/"], generated_project)
    assert result.returncode == 0, f"ruff check:\n{result.stdout}\n{result.stderr}"


def test_ruff_format_passes(generated_project: Path):
    result = _run(["uvx", "ruff", "format", "--check", "src/", "tests/"], generated_project)
    assert result.returncode == 0, f"ruff format:\n{result.stdout}\n{result.stderr}"


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("java") is None, reason="Java is required to run PySpark")
def test_generated_unit_tests_pass(generated_project: Path):
    result = _run(["uv", "run", "--extra", "dev", "pytest", "tests/unit/", "-q"], generated_project)
    assert result.returncode == 0, f"pytest:\n{result.stdout[-5000:]}\n{result.stderr[-2000:]}"
