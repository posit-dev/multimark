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

.PHONY: dist-wheel
dist-wheel: clean ## builds native abi3 wheel using cibuildwheel
	pip install cibuildwheel==2.23.4
	python -m cibuildwheel --output-dir dist
	ls -l dist

.PHONY: dist-pyodide
dist-pyodide: clean ## builds Pyodide/emscripten wheel (requires Linux or macOS)
	pip install pyodide-build
	pyodide build --outdir dist
	ls -l dist

.PHONY: dist-sdist
dist-sdist: clean ## builds source distribution only
	pip install build
	python3 -m build --sdist
	ls -l dist

.PHONY: dist-all
dist-all: clean ## builds native wheel, Pyodide wheel, and sdist
	pip install cibuildwheel==2.23.4 pyodide-build build
	python -m cibuildwheel --output-dir dist
	pyodide build --outdir dist
	python3 -m build --sdist --outdir dist
	ls -l dist
