# databricks-pyspark-bundle-template

[Copier](https://copier.readthedocs.io/) template for PySpark jobs deployed on Databricks with Asset Bundles.

## What you get

- A Databricks Asset Bundle (`databricks.yml`) with `dev` / `staging` / `prod` targets; per-environment
  settings (catalog, schema, log level) are bundle variables passed to the job
- A Python wheel run by a `python_wheel_task`, on **serverless** compute or a **job cluster** (chosen at generation)
- Personal dev copies: `[dev <you>]` job, paused schedule, `dev_<you>` schema
- Unit tests on local Spark + Delta, integration tests on the workspace through Databricks Connect,
  both pinned to the Spark / Python version of the chosen compute
- GitHub Actions: lint, unit tests, bundle validate; on `main` deploy staging, run the job and the
  integration tests; on `v*` tags deploy prod. Auth with a service principal (OAuth M2M)

## Usage

```bash
uvx copier copy --trust gh:jordansportes8355/databricks-pyspark-bundle-template my-project
```

Supported compute (local Python / Spark / Databricks Connect versions are derived automatically):

| Compute | Python | Spark | Databricks Connect |
| --- | --- | --- | --- |
| Serverless env 2 | 3.11 | 3.5 | 15.4 |
| Serverless env 3 | 3.12 | 3.5 | 16.4 |
| Serverless env 4 | 3.12 | 4.0 | 17.3 |
| Serverless env 5 (default) | 3.12 | 4.1 | 18 |
| Job cluster DBR 14.3 LTS | 3.10 | 3.5 | 14.3 |
| Job cluster DBR 15.4 LTS | 3.11 | 3.5 | 15.4 |
| Job cluster DBR 16.4 LTS | 3.12 | 3.5 | 16.4 |
| Job cluster DBR 17.3 LTS | 3.12 | 4.0 | 17.3 |
| Job cluster DBR 18 LTS | 3.12 | 4.1 | 18 |

To support a new runtime, add a line to the `runtime` matrix in `copier.yml`.

Update an existing project to the latest template version:

```bash
uvx copier update --trust
```

## Developing the template

```bash
uv sync
uv run pytest                 # generated unit tests need Java; bundle tests need the Databricks CLI
uv run pytest -m "not slow"   # generation checks only
```
