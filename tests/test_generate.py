"""Tests for template generation correctness."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

PKG = "src/test_spark_job"

EXPECTED_FILES = [
    ".copier-answers.yml",
    ".env.example",
    ".github/workflows/ci.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".python-version",
    "Makefile",
    "README.md",
    "databricks.yml",
    "pyproject.toml",
    "resources/test_spark_job_job.yml",
    *(
        f"{PKG}/{f}"
        for f in [
            "__init__.py",
            "config.py",
            "io.py",
            "logger.py",
            "main.py",
            "secrets.py",
            "spark.py",
            "conf/base.yaml",
            "conf/dev.yaml",
            "conf/staging.yaml",
            "jobs/__init__.py",
            "jobs/example_job.py",
            "transformations/__init__.py",
            "transformations/example.py",
        ]
    ),
    "tests/conftest.py",
    *(
        f"tests/unit/{f}"
        for f in [
            "__init__.py",
            "test_config.py",
            "test_example_job.py",
            "test_example_transform.py",
            "test_io.py",
            "test_logger.py",
            "test_secrets.py",
            "test_spark.py",
        ]
    ),
]


def _files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def test_generated_files_match_expected(generated_project: Path):
    assert _files(generated_project) == set(EXPECTED_FILES)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("pyproject.toml", 'description = "Test Spark Job"'),
        ("resources/test_spark_job_job.yml", "test@example.com"),
        (f"{PKG}/conf/base.yaml", 'catalog: "test_catalog"'),
        (f"{PKG}/conf/dev.yaml", 'catalog: "test_catalog_dev"'),
    ],
)
def test_answers_are_rendered(generated_project: Path, path: str, expected: str):
    assert expected in (generated_project / path).read_text()


def test_ci_yml_keeps_github_expressions(generated_project: Path):
    """GitHub Actions expressions must be preserved, not mangled by Copier."""
    content = (generated_project / ".github/workflows/ci.yml").read_text()
    assert "${{ secrets.DATABRICKS_HOST }}" in content
    assert "raw" not in content  # jinja raw tags must not leak into output


def test_answers_file_enables_copier_update(generated_project: Path):
    answers = yaml.safe_load((generated_project / ".copier-answers.yml").read_text())
    assert answers["_src_path"]
    assert answers["_commit"]
    assert answers["package_name"] == "test_spark_job"
    assert "runtime" not in answers  # computed values must not be frozen in answers


@pytest.mark.parametrize(
    ("cloud", "node_type"),
    [("aws", "m5.xlarge"), ("azure", "Standard_DS3_v2"), ("gcp", "n2-standard-4")],
)
def test_node_type_per_cloud(make_project, cloud: str, node_type: str):
    project = make_project(cloud_provider=cloud)
    assert f"default: {node_type}" in (project / "databricks.yml").read_text()


@pytest.mark.parametrize(
    ("runtime", "python", "pyspark", "spark_version", "java"),
    [
        ("14.3", "3.10", "pyspark>=3.5,<3.6", "14.3.x-scala2.12", "17"),
        ("15.4", "3.11", "pyspark>=3.5,<3.6", "15.4.x-scala2.12", "17"),
        ("16.4", "3.12", "pyspark>=3.5,<3.6", "16.4.x-scala2.12", "17"),
        ("17.3", "3.12", "pyspark>=4.0,<4.1", "17.3.x-scala2.13", "17"),
        ("18", "3.12", "pyspark>=4.1,<4.2", "18.x-scala2.13", "21"),
    ],
)
def test_versions_follow_runtime(make_project, runtime: str, python: str, pyspark: str, spark_version: str, java: str):
    project = make_project(databricks_runtime=runtime)
    pyproject = (project / "pyproject.toml").read_text()

    assert (project / ".python-version").read_text().strip() == python
    assert f'requires-python = ">={python}"' in pyproject
    assert f'"{pyspark}"' in pyproject
    assert f'spark_version: "{spark_version}"' in (project / "resources/test_spark_job_job.yml").read_text()
    assert f'java-version: "{java}"' in (project / ".github/workflows/ci.yml").read_text()


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
def test_validators_reject_invalid_answers(make_project, bad_answer: dict[str, str]):
    with pytest.raises(ValueError):
        make_project(**bad_answer)


# ── Generated project quality gates (mirror the generated CI) ─────────────────


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("cmd", [["check"], ["format", "--check"]], ids=["check", "format"])
def test_ruff_passes(generated_project: Path, cmd: list[str]):
    result = _run(["uvx", "ruff", *cmd, "src/", "tests/"], generated_project)
    assert result.returncode == 0, f"ruff {cmd}:\n{result.stdout}\n{result.stderr}"


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("java") is None, reason="Java is required to run PySpark")
def test_generated_unit_tests_pass(generated_project: Path):
    result = _run(["uv", "run", "pytest", "tests/unit/", "-q"], generated_project)
    assert result.returncode == 0, f"pytest:\n{result.stdout[-5000:]}\n{result.stderr[-2000:]}"
