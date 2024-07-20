# Development

Refer to Makefile

## Migrations

Autogenerating migrations can be done by dropping into a poetry shell, adding pass env var,
and running revision generate. e.g.:

```
env $(cat ../.env) poetry shell
alembic revision --autogenerate -m "init"
```