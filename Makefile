.DEFAULT_GOAL := help
.PHONY: help sync test test-file cov lint lint-file fmt typecheck hooks changelog-lint \
        build run version install-local uninstall-local npm-test npm-pack npm-publish tag

UV ?= uv
FILE ?= tests/linter_test.py
PYFILE ?= src/keepmeachangelog/cli.py
VERSION := $(shell $(UV) run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])' 2>/dev/null)

help: ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)

## ---- Setup ----------------------------------------------------------------
sync: ## Install dev and test dependencies
	$(UV) sync --group dev --group test

## ---- Tests (the full suite is heavy: prefer test-file while developing) ----
test-file: ## Run one test file, no coverage: make test-file FILE=tests/linter_test.py
	nice -n 19 $(UV) run pytest $(FILE) -q --no-cov

test: ## Full test suite (with the 100% coverage gate)
	nice -n 19 $(UV) run pytest

cov: ## Coverage report in the terminal (+ coverage.xml)
	nice -n 19 $(UV) run pytest --cov-report=term-missing

## ---- Quality --------------------------------------------------------------
lint-file: ## Ruff + pyright on one file: make lint-file PYFILE=src/keepmeachangelog/cli.py
	ruff check $(PYFILE)
	$(UV) run pyright $(PYFILE)

typecheck: ## Pyright on src and tests
	$(UV) run pyright

lint: ## All pre-commit hooks on every file (the full gate)
	pre-commit run --all-files

fmt: ## Format with ruff
	ruff format src tests scripts

hooks: ## Install the git pre-commit hooks
	pre-commit install

changelog-lint: ## Lint this repo's CHANGELOG.md against pyproject.toml's version
	$(UV) run keepmeachangelog --validation-depth 10 --version-from pyproject.toml CHANGELOG.md

## ---- Run / install ----------------------------------------------------------
run: ## Run the linter on a path: make run ARGS=". --fix"
	$(UV) run keepmeachangelog $(ARGS)

version: ## Show the project version (pyproject.toml and npm/package.json)
	@echo "python: $(VERSION)"
	@node -p '"npm:    " + require("./npm/package.json").version'

install-local: ## Install the CLI globally from this checkout (EDITABLE=1 to track the code)
	$(UV) tool install --reinstall $(if $(EDITABLE),--editable) .

uninstall-local: ## Remove the global CLI
	$(UV) tool uninstall keepmeachangelog

## ---- Build / npm ------------------------------------------------------------
build: ## Build the Python sdist and wheel into dist/
	$(UV) build

npm-test: ## Run the npm wrapper tests
	cd npm && npm test

npm-pack: ## Dry-run the npm tarball (shows what would be published)
	cd npm && npm pack --dry-run

npm-publish: npm-test ## Publish the npm wrapper: make npm-publish OTP=123456 (needs `npm login`)
	@test -n "$(OTP)" || { echo "usage: make npm-publish OTP=<6-digit code>" >&2; exit 2; }
	cd npm && npm publish --access public --otp=$(OTP)

## ---- Release ------------------------------------------------------------------
tag: changelog-lint ## Create the annotated tag v<version> (does not push)
	@test "$$(node -p 'require("./npm/package.json").version')" = "$(VERSION)" \
		|| { echo "npm/package.json version differs from pyproject.toml" >&2; exit 1; }
	git tag -a v$(VERSION) -m "v$(VERSION)"
	@echo "created v$(VERSION); publish with: git push origin main v$(VERSION)"
