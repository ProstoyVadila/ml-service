# === Params ===
APP_MAIN=main.py
ENV_FILE=.env
UV=uv
ALEMBIC=$(UV) run alembic
MIGRATIONS_DIR=migrations

.PHONY: run test lint lint-fix format audit install upgrade-deps clean pre-commit \
        migrate makemigrations downgrade show heads current

run:
	PYTHONPATH=. $(UV) run python $(APP_MAIN)

test:
	@$(UV) run pytest tests -v --tb=short

lint:
	@$(UV) run ruff check .

lint-fix:
	@$(UV) run ruff check --fix .

format:
	@$(UV) run ruff format .

audit:
	@$(UV) run pip-audit

install:
	@$(UV) pip install --system

upgrade-deps:
	@$(UV) pip compile pyproject.toml --upgrade --all-extras

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete

pre-commit:
	@$(UV) run pre-commit run --all-files

# === Alembic ===
migrate:
	@$(ALEMBIC) upgrade head

makemigrations:
	@read -p "Enter migration message: " msg; \
	$(ALEMBIC) revision --autogenerate -m "$$msg"

downgrade:
	@$(ALEMBIC) downgrade -1

show:
	@$(ALEMBIC) history --verbose

current:
	@$(ALEMBIC) current

heads:
	@$(ALEMBIC) heads
