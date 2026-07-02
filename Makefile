.PHONY: up down seed test
up:
	docker compose up -d
down:
	docker compose down
seed:
	uv run python -m dojo.seed
test:
	uv run --extra dev pytest
