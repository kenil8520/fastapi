# fastapi
alembic revision --autogenerate -m "initial"

run migration

alembic upgrade head