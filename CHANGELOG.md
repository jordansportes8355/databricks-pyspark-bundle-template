# Changelog

## Unreleased

- Generated project passes `ruff format --check` (CI was red on first push)
- `databricks_runtime` is now a choice of LTS versions; Python, PySpark, Delta and Scala versions are derived from it
- `.copier-answers.yml` generated so projects can use `copier update`
- Local Spark session loads Delta jars via `configure_spark_with_delta_pip`; Delta round-trip tests added
- `get_spark` detects Databricks via `DATABRICKS_RUNTIME_VERSION` and applies the `spark` config section
- Config uses plain pydantic models; `unity_catalog.schema` is now required
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
