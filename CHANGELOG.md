# Changelog

## v0.1.0

- Initial release
- Copier template targeting AWS Databricks (Asset Bundles)
- Multi-env YAML config (dev / staging / prod) embedded in wheel
- Unity Catalog Delta I/O helpers
- Databricks secret scope integration with local env-var fallback
- SparkSession factory: active session on Databricks, local builder for tests
- Unit test fixtures using local[1] SparkSession + Delta
- GitHub Actions CI: ruff lint, pytest, bundle validate, deploy staging on main
