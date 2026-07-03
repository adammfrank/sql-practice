.PHONY: up down seed test plan FORCE
up:
	docker compose up -d
down:
	docker compose down
seed:
	uv run python -m dojo.seed

# `make test`                       -> run every lesson's test
# `make test lessons/04_left_prefix` -> run just that lesson's test
test:
	uv run --extra dev pytest $(filter-out test,$(MAKECMDGOALS))

# `make plan lessons/04_left_prefix` -> apply that lesson's indexes.sql +
# solution.sql against a throwaway clone and print the EXPLAIN plan (no gate)
plan:
	uv run python -m dojo.plan_lesson $(filter-out plan,$(MAKECMDGOALS))

# Let a lesson path be passed as a positional argument to the targets above
# without Make trying to build it as a target. The FORCE prerequisite keeps
# it a silent no-op even though the directory already exists (otherwise Make
# prints "'lessons/...' is up to date").
lessons/%: FORCE
	@:
FORCE:
