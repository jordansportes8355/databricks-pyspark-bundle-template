"""Tests for template generation correctness."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from conftest import DEFAULT_ANSWERS, JOB_CLUSTER

PKG = "src/test_spark_job"
JOB_YML = "resources/test_spark_job_job.yml"

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
    JOB_YML,
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
            "jobs/__init__.py",
            "jobs/example_job.py",
            "transformations/__init__.py",
            "transformations/example.py",
        ]
    ),
    "tests/conftest.py",
    "tests/integration/__init__.py",
    "tests/integration/conftest.py",
    "tests/integration/test_example_job.py",
    *(
        f"tests/unit/{f}"
        for f in [
            "__init__.py",
            "test_config.py",
            "test_example_job.py",
            "test_example_transform.py",
            "test_io.py",
            "test_logger.py",
            "test_main.py",
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
        (JOB_YML, "test@example.com"),
        ("databricks.yml", "default: test_catalog"),
        ("databricks.yml", "schema: dev_${workspace.current_user.short_name}"),
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


# ── Compute-specific rendering ────────────────────────────────────────────────


def test_serverless_job_uses_environment(make_project):
    job = (make_project(serverless_environment="4") / JOB_YML).read_text()
    assert 'environment_version: "4"' in job
    assert "environment_key: default" in job
    assert "new_cluster" not in job


@pytest.mark.parametrize(
    ("cloud", "node_type"),
    [("aws", "m5.xlarge"), ("azure", "Standard_DS3_v2"), ("gcp", "n2-standard-4")],
)
def test_job_cluster_node_type_per_cloud(make_project, cloud: str, node_type: str):
    project = make_project(**{**JOB_CLUSTER, "cloud_provider": cloud})
    assert f"default: {node_type}" in (project / "databricks.yml").read_text()
    assert "environments:" not in (project / JOB_YML).read_text()


@pytest.mark.parametrize(
    ("answers", "python", "pyspark", "dbconnect", "java"),
    [
        pytest.param({"serverless_environment": "2"}, "3.11", ">=3.5,<3.6", ">=15.4,<15.5", "17", id="env2"),
        pytest.param({"serverless_environment": "3"}, "3.12", ">=3.5,<3.6", ">=16.4,<16.5", "17", id="env3"),
        pytest.param({"serverless_environment": "4"}, "3.12", ">=4.0,<4.1", ">=17.3,<17.4", "17", id="env4"),
        pytest.param({"serverless_environment": "5"}, "3.12", ">=4.1,<4.2", ">=18.0,<19", "21", id="env5"),
        pytest.param(
            {**JOB_CLUSTER, "databricks_runtime": "14.3"}, "3.10", ">=3.5,<3.6", ">=14.3,<14.4", "17", id="dbr14.3"
        ),
        pytest.param(
            {**JOB_CLUSTER, "databricks_runtime": "15.4"}, "3.11", ">=3.5,<3.6", ">=15.4,<15.5", "17", id="dbr15.4"
        ),
        pytest.param(
            {**JOB_CLUSTER, "databricks_runtime": "16.4"}, "3.12", ">=3.5,<3.6", ">=16.4,<16.5", "17", id="dbr16.4"
        ),
        pytest.param(
            {**JOB_CLUSTER, "databricks_runtime": "17.3"}, "3.12", ">=4.0,<4.1", ">=17.3,<17.4", "17", id="dbr17.3"
        ),
        pytest.param({**JOB_CLUSTER, "databricks_runtime": "18"}, "3.12", ">=4.1,<4.2", ">=18.0,<19", "21", id="dbr18"),
    ],
)
def test_local_stack_matches_compute(make_project, answers, python, pyspark, dbconnect, java):
    project = make_project(**answers)
    pyproject = (project / "pyproject.toml").read_text()

    assert (project / ".python-version").read_text().strip() == python
    assert f'requires-python = "~={python}.0"' in pyproject
    assert f'"pyspark{pyspark}"' in pyproject
    assert f'"databricks-connect{dbconnect}"' in pyproject
    assert f'java-version: "{java}"' in (project / ".github/workflows/ci.yml").read_text()


@pytest.mark.parametrize(
    ("runtime", "spark_version"),
    [("16.4", "16.4.x-scala2.12"), ("17.3", "17.3.x-scala2.13"), ("18", "18.x-scala2.13")],
)
def test_job_cluster_spark_version(make_project, runtime: str, spark_version: str):
    project = make_project(**{**JOB_CLUSTER, "databricks_runtime": runtime})
    assert f'spark_version: "{spark_version}"' in (project / JOB_YML).read_text()


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


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, env=env)


@pytest.mark.parametrize("cmd", [["check"], ["format", "--check"]], ids=["check", "format"])
def test_ruff_passes(generated_project: Path, cmd: list[str]):
    result = _run(["uvx", "ruff", *cmd, "src/", "tests/"], generated_project)
    assert result.returncode == 0, f"ruff {cmd}:\n{result.stdout}\n{result.stderr}"


@pytest.mark.skipif(shutil.which("databricks") is None, reason="Databricks CLI not installed")
@pytest.mark.parametrize("target", ["dev", "staging", "prod"])
def test_bundle_validates(generated_project: Path, databricks_api: str, tmp_path: Path, target: str):
    """`databricks bundle validate` against a fake workspace API: config, variables and paths resolve."""
    project = shutil.copytree(generated_project, tmp_path / "bundle")
    bundle_yml = project / "databricks.yml"
    bundle_yml.write_text(bundle_yml.read_text().replace(DEFAULT_ANSWERS["databricks_host"], databricks_api))
    env = {k: v for k, v in os.environ.items() if not k.startswith("DATABRICKS_")}
    env |= {"DATABRICKS_TOKEN": "fake", "DATABRICKS_CONFIG_FILE": str(tmp_path / "none.cfg")}

    text = _run(["databricks", "bundle", "validate", "-t", target], project, env)
    assert text.returncode == 0, text.stdout + text.stderr
    assert "Warning:" not in text.stdout + text.stderr

    resolved = json.loads(_run(["databricks", "bundle", "validate", "-t", target, "-o", "json"], project, env).stdout)
    task = resolved["resources"]["jobs"]["test_spark_job_job"]["tasks"][0]
    params = task["python_wheel_task"]["parameters"]
    expected_schema = {"dev": "dev_jane_doe", "staging": "test_spark_job_staging", "prod": "test_spark_job"}
    assert params[params.index("--schema") + 1] == expected_schema[target]
    assert params[params.index("--catalog") + 1] == "test_catalog"

    environments = resolved["resources"]["jobs"]["test_spark_job_job"].get("environments", [])
    wheels = [lib["whl"] for lib in task.get("libraries", [])]
    wheels += [dep for env_ in environments for dep in env_["spec"]["dependencies"]]
    assert wheels and all(w.removeprefix("./") == "dist/*.whl" for w in wheels), wheels


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("java") is None, reason="Java is required to run PySpark")
def test_generated_unit_tests_pass(generated_project: Path):
    result = _run(["uv", "run", "pytest", "-q"], generated_project)
    assert result.returncode == 0, f"pytest:\n{result.stdout[-5000:]}\n{result.stderr[-2000:]}"
    assert "2 skipped" in result.stdout  # integration tests need databricks-connect
