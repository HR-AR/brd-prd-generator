.PHONY: lint test type-check validate install clean

install:
	pip install -r requirements.txt

lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

test:
	pytest tests/ -v

validate: lint type-check test
	@echo "✓ All validation checks passed"

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete