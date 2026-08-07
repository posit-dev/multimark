.PHONY: test
test: ## Run tests
	@pytest tests \
		--durations 10

.PHONY: lint
lint: ## Run ruff formatter and linter
	@ruff format
	@ruff check --fix

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .pytest_cache

dist: clean ## builds source and wheel package
	python3 -m build
	ls -l dist

.PHONY: dist-pyodide
dist-pyodide: clean ## builds Pyodide/emscripten wheel (requires Linux or macOS)
	pip install pyodide-build
	pyodide build --outdir dist
	ls -l dist
