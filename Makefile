.PHONY: up down seed test
up:
	docker compose up -d
down:
	docker compose down
seed:
	.venv/Scripts/python -m dojo.seed
test:
	.venv/Scripts/pytest
