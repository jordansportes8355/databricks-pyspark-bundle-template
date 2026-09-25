# Changelog

## v0.3.0

Databricks-only, bundle-first:
- Repository renamed `pyspark-template` → `databricks-pyspark-bundle-template`
- Compute chosen at generation: serverless (environment 2–5) or job cluster (DBR 14.3–18 LTS)
- Per-environment settings moved from YAML files to bundle variables passed as job parameters;
  `conf/` and the `pyyaml` dependency removed
- Personal dev schema `dev_<user>`; the job creates its schema if missing
- Example job reads `samples.nyctaxi.trips`, so it runs out of the box on any workspace
- Databricks Connect: `dbconnect` dependency group (separate `.venv-dbconnect`), `get_spark` uses it
  when installed, integration tests in `tests/integration`, `make test-integration`
- CI on `main`: deploy staging, run the job, run integration tests

Fixes:
- Wheel path in the job resource resolved to `resources/dist/*.whl` (now `../dist/*.whl`)
- staging / prod `root_path` in `/Workspace/Shared` was writable by all users; now the deploying identity's folder

Tests:
- Both compute types rendered and checked; `databricks bundle validate` run for every target against a fake
  workspace API

## v0.2.0

Lighter generated project:
- Config parsed into frozen dataclasses (DBR 14.3/15.4 ship pydantic 1.x): unknown or missing keys fail fast
- `io/reader.py` + `io/writer.py` merged into `io.py`; logging configured in Python (no `logging.yaml`); no `prod.yaml` (base = prod)
- `[dependency-groups] dev` instead of extras: plain `uv sync` / `uv run pytest`; `chispa` removed
- Makefile trimmed; staging / prod deploys only through CI
- Runtime stack defined once in a `runtime` matrix in `copier.yml`

Fixes and additions:
- DBR 18 LTS (Spark 4.1, Java 21)
- `.python-version` generated so local Python matches the cluster
- `get_secret` uses the cluster session on Databricks, no silent env-var fallback there
- Tests for secrets and logging
- Generated project passes `ruff format --check` (CI was red on first push)
- `databricks_runtime` is now a choice of LTS versions; Python, PySpark, Delta and Scala versions are derived from it
- `.copier-answers.yml` generated so projects can use `copier update`
- Local Spark session loads Delta jars via `configure_spark_with_delta_pip`; Delta round-trip tests added
- `get_spark` detects Databricks via `DATABRICKS_RUNTIME_VERSION` and applies the `spark` config section
- `unity_catalog.schema` is now required
- Job resource renamed `<package_name>_job`; `num_workers` per target; `root_path` and `permissions` on staging/prod
- CI: pinned actions, explicit Java, OAuth service principal auth, prod deploy on `v*` tags
- Answer validators, README and `.env.example` in generated project, template CI and README

## v0.1.0

- Initial release
- Copier template targeting AWS Databricks (Asset Bundles)
- Multi-env YAML config (dev / staging / prod) embedded in wheel
- Unity Catalog Delta I/O helpers
- Databricks secret scope integration with local env-var fallback
- SparkSession factory: active session on Databricks, local builder for tests
- Unit test fixtures using local[1] SparkSession + Delta
- GitHub Actions CI: ruff lint, pytest, bundle validate, deploy staging on main
