.PHONY: up down seed test plan lab lab-clean FORCE
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

# `make lab lessons/07_statistics` -> create a persistent clone
# (dojo_lab_<name>) with the lesson's indexes.sql + setup.sql applied, then
# open a psql session in it for hands-on EXPLAIN/ANALYZE experimenting.
# `make lab-clean` drops every dojo_lab_* database.
lab:
	uv run python -m dojo.lab $(filter-out lab,$(MAKECMDGOALS))
lab-clean:
	uv run python -m dojo.lab --clean

# Let a lesson path be passed as a positional argument to the targets above
# without Make trying to build it as a target. The FORCE prerequisite keeps
# it a silent no-op even though the directory already exists (otherwise Make
# prints "'lessons/...' is up to date").
lessons/%: FORCE
	@:
FORCE:
