.PHONY: format lint test hooks run

format:
	black .
	ruff --fix .

lint:
	ruff .
	black --check .

test:
	pytest -q

hooks:
	pre-commit install

run:
	python -m praevion_core.interfaces.cli.main
