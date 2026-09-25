# pyspark-template

[Copier](https://copier.readthedocs.io/) template for PySpark jobs deployed on Databricks with Asset Bundles.

## What you get

- `src/` package built as a wheel and run as a `python_wheel_task`
- Multi-env YAML config (`dev` / `staging` / `prod`) parsed into frozen dataclasses, no extra dependency
- Unity Catalog Delta I/O helpers, secret scopes with env-var fallback, JSON logging
- Local Spark + Delta session for unit tests, versions pinned to the chosen Databricks Runtime
- GitHub Actions: lint, format, tests, bundle validate, deploy staging on `main`, prod on `v*` tags

## Usage

```bash
uvx copier copy --trust gh:jordansportes8355/pyspark-template my-project
```

Supported runtimes (Python / Spark / Delta versions are derived automatically):

| DBR LTS | Python | Spark | Delta |
| --- | --- | --- | --- |
| 14.3 | 3.10 | 3.5 | 3.2–3.3 |
| 15.4 | 3.11 | 3.5 | 3.2–3.3 |
| 16.4 | 3.12 | 3.5 | 3.2–3.3 |
| 17.3 | 3.12 | 4.0 | 4.0 |
| 18 | 3.12 | 4.1 | 4.2 |

To support a new runtime, add a line to the `runtime` matrix in `copier.yml`.

Update an existing project to the latest template version:

```bash
uvx copier update --trust
```

## Developing the template

```bash
uv sync
uv run pytest                 # needs Java 17 for the generated-project unit tests
uv run pytest -m "not slow"   # generation checks only
```
