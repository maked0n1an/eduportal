# Makefile

# Include the prepare-env.mk file
# prepare-env.mk

.PHONY: prepare-env

prepare-env:
	@echo Creating .env config
	@if not exist .env copy .env.example .env >nul 2>&1

dbs-up:
	@docker compose -f docker-compose.yaml up -d
	@echo Waiting 2 secs for Postgres to be ready...
	@timeout /T 2 /NOBREAK > NUL
	@alembic upgrade head

dbs-down:
	docker compose -f docker-compose.yaml down && docker network prune --force
