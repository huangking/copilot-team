PY ?= python3
.DEFAULT_GOAL := test

.PHONY: test lint run clean

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m compileall -q src tests

run:
	PYTHONPATH=src $(PY) -m taskboard list

clean:
	rm -rf .pytest_cache src/taskboard/__pycache__ tests/__pycache__
