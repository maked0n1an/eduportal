up:
	docker compose -f docker-compose.yaml up -d
	echo Waiting 2 sec for Postgres to be ready...
	timeout /T 2 /NOBREAK > NUL
	alembic upgrade head

down:
	docker compose -f docker-compose.yaml down && docker network prune --force
