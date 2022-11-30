#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PWD := `pwd`

#* Docker variables
PROJECT := fullfeedfilter
PROJECT_TITLE := Fullfeedfilter
VERSION := latest
PYINSTALLER_ENTRY := $(PROJECT)/__main__.py

# poetry show black2 &> /dev/null && echo "true" || echo "false"


#-----------------------------------------------------------------------------------------
# DEV INSTALLATION
#-----------------------------------------------------------------------------------------
.PHONY: install-poetry
install-poetry: ## Download and install Poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) -

.PHONY: uninstall-poetry
uninstall-poetry: ## Uninstall Poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) - --uninstall

.PHONY: install-pyinstaller
install-pyinstaller: ## Download and install PyInstaller
	poetry run sudo apt install libpython3.10-dev -y
	poetry add --group dev pyinstaller@latest pillow@latest

.PHONY: remove-pyinstaller
remove-pyinstaller: ## Uninstall PyInstaller
	poetry remove --group dev pyinstaller@latest pillow@latest

.PHONY: install-pre-commit-hooks
install-pre-commit-hooks: ## Install Pre-Commit Git Hooks
	poetry run pre-commit install

.PHONY: install-pyqt5
install-pyqt5: ## Install PyQt5
	poetry add PyQt5@latest

#-----------------------------------------------------------------------------------------
# INSTALL/UPDATE DEPENDENCIES/REQUIREMENTS
#-----------------------------------------------------------------------------------------

.PHONY: install
install: ## Install Project Dependecies/Requirements from Poetry
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n
	-poetry run mypy --install-types --non-interactive ./

.PHONY: update-dev-deps
update-dev-deps: ## Update dev dependecies to @latest version
	poetry add --group dev  bandit@latest darglint@latest "isort[colors]@latest" mypy@latest pre-commit@latest pydocstyle@latest pylint@latest pytest@latest pyupgrade@latest safety@latest coverage@latest coverage-badge@latest pytest-html@latest pytest-cov@latest
	poetry add --group dev  --allow-prereleases black@latest

#-----------------------------------------------------------------------------------------
# ORIGINAL INSTALLATION HOOKS
#-----------------------------------------------------------------------------------------
.PHONY: poetry-download
poetry-download: install-poetry ## Download and install Poetry

.PHONY: pre-commit-install
pre-commit-install: install-pre-commit-hooks ## Install Pre-Commit Git Hooks

#-----------------------------------------------------------------------------------------
# Linting, Formatting, TypeCheck
#-----------------------------------------------------------------------------------------
.PHONY: lint
lint: test check-codestyle mypy check-safety ## Lint, Format, Check Types, Check Safety

.PHONY: formatting
formatting: codestyle ## Apply Formatting via PyUpgrade, ISort, Black.

.PHONY: codestyle
codestyle: ## Apply Formatting via PyUpgrade, ISort, Black.
	poetry run pyupgrade --exit-zero-even-if-changed --py310-plus **/*.py
	poetry run isort --settings-path pyproject.toml ./
	poetry run black --config pyproject.toml ./

.PHONY: check-codestyle
check-codestyle: ## Check Formatting via ISort, Black, darglint.
	poetry run isort --diff --check-only --settings-path pyproject.toml ./
	poetry run black --diff --check --config pyproject.toml ./
	poetry run darglint --verbosity 2 $(PROJECT) tests

.PHONY: check-safety
check-safety: ## Check Securty & Safty via Bandit, Safety.
	poetry check
	poetry run safety check --full-report
	poetry run bandit -ll --recursive $(PROJECT) tests

.PHONY: mypy
mypy: ## Typechecking via MyPy
	poetry run mypy --config-file pyproject.toml ./


#-----------------------------------------------------------------------------------------
# TESTS
#-----------------------------------------------------------------------------------------
.PHONY: tests
tests: test ## Run Tests & Coverage

.PHONY: test
test: ## Run Tests & Coverage
	PWD=$(PWD) poetry run pytest -c pyproject.toml --cov-report=html --cov=$(PROJECT) tests/
	poetry run coverage-badge -o assets/images/coverage.svg -f


#-----------------------------------------------------------------------------------------
# BUILD PACKAGE
#-----------------------------------------------------------------------------------------
.PHONY: build-package
build-package: ## Build as Package
	poetry build


#-----------------------------------------------------------------------------------------
# BUILD EXECUTABLE
#-----------------------------------------------------------------------------------------
.PHONY: build-pyinstaller-linux
build-pyinstaller-linux: ## Build Linux Executable
	pyinstaller $(PYINSTALLER_ENTRY) \
		--clean \
		--onefile \
		--windowed \
		--paths=$(PWD)/$(PROJECT) \
		--icon=$(PWD)/assets/images/icon.png \
		--workpath=$(PWD)/build_linux \
		--distpath=$(PWD)/dist_linux \
		--name=$(PROJECT) \
		--copy-metadata=$(PROJECT)

.PHONY: build-pyinstaller-win
build-pyinstaller-win: ## Build Windows Executable
	pyinstaller $(PYINSTALLER_ENTRY) \
		--clean \
		--onefile \
		--windowed \
		--paths=$(PWD)/$(PROJECT) \
		--icon=$(PWD)/assets/images/icon.png \
		--workpath=$(PWD)/build_win \
		--distpath=$(PWD)/dist_win \
		--name=$(PROJECT) \
		--copy-metadata=$(PROJECT)


#-----------------------------------------------------------------------------------------
# BUILD RESOURCES
#-----------------------------------------------------------------------------------------
.PHONY: build-pyqt5-resources
build-pyqt5-resources: ## Build PyQt5 Resources File
	pyrcc5 $(PWD)/assets/ui/resources.qrc -o $(PWD)/$(PROJECT)/resources_rc.py

.PHONY: build-pyqt5-ui
build-pyqt5-ui: ## Build PyQt5 QtDesigner UI File
	pyuic5 -x $(PWD)/assets/ui/pyqt5_ui.ui -o $(PWD)/$(PROJECT)/pyqt5_ui.py

.PHONY: build-desktop-file
build-desktop-file: ## Build .desktop File
	printf "[Desktop Entry]\nName=$(PROJECT_TITLE)\nIcon=$(PWD)/assets/images/icon.png\nType=Application\nExec=$(PWD)/dist_linux/$(PROJECT)\nTerminal=false" > "$(PWD)/dist_linux/$(PROJECT).desktop"



#-----------------------------------------------------------------------------------------
# INSTALL EXECUTABLE, SHORTCUTS, RESOURCES
#-----------------------------------------------------------------------------------------
.PHONY: install-linux
install-linux: install-linux-executable install-linux-user-config  install-desktop-file ## Full Installl of Executable, User Config(won't overwrite), Desktop File
	echo "Completed Install."

.PHONY: install-linux-executable
install-linux-executable: ## Installs binary in ~/bin
	mkdir -p $(HOME)/bin
	ln -sfv $(PWD)/dist_linux/$(PROJECT) /home/${USER}/bin/$(PROJECT)

.PHONY: install-linux-user-config
install-linux-user-config: ## Installs config in ~/.vapps
	test -f $(PWD)/$(PROJECT)/.vapps/$(PROJECT).yaml && mkdir -p $(HOME)/.vapps || echo ""
	test -f $(PWD)/$(PROJECT)/.vapps/$(PROJECT).yaml && cp -n $(PWD)/$(PROJECT)/.vapps/$(PROJECT).yaml $(HOME)/.vapps/$(PROJECT).yaml || echo ""

.PHONY: install-desktop-file
install-desktop-file: build-desktop-file ## Install .desktop shortcut for user
	desktop-file-install --dir=$(HOME)/.local/share/applications "$(PWD)/dist_linux/$(PROJECT).desktop"
	update-desktop-database $(HOME)/.local/share/applications

.PHONY: update-desktop-database
update-desktop-database: ## Updates Linux database of .desktop shortcuts
	update-desktop-database $(HOME)/.local/share/applications



#-----------------------------------------------------------------------------------------
# DJANGO
#-----------------------------------------------------------------------------------------
.PHONY: django-migrate
django-migrate: ## Applies Django Migrations
	poetry run python "$(PWD)/$(PROJECT)/manage.py" migrate
	poetry run python "$(PWD)/$(PROJECT)/manage.py" makemigrations

.PHONY: django-createsuperuser
django-createsuperuser: ## Creates a Django Superuser
	poetry run python "$(PWD)/$(PROJECT)/manage.py" createsuperuser

.PHONY: django-runserver
django-runserver: ## Runs Django Server
	poetry run python $(PWD)/$(PROJECT)/manage.py runserver

#-----------------------------------------------------------------------------------------
# DOCKER
#-----------------------------------------------------------------------------------------
# Example: make docker-build VERSION=latest
# Example: make docker-build PROJECT=some_name VERSION=0.0.1
.PHONY: docker-build
docker-build: ## Build a docker image from Dockerfile
	@echo Building docker $(PROJECT):$(VERSION) ...
	docker build \
		-t $(PROJECT):$(VERSION) . \
		-f ./Dockerfile

# Example: make docker-remove VERSION=latest
# Example: make docker-remove PROJECT=some_name VERSION=0.0.1
.PHONY: docker-remove
docker-remove: ## Remove Docker Image
	@echo Removing docker $(PROJECT):$(VERSION) ...
	docker rmi -f $(PROJECT):$(VERSION)


#-----------------------------------------------------------------------------------------
# CLEANUP
#-----------------------------------------------------------------------------------------
.PHONY: cleanup
cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove ## Complete Cleanup

.PHONY: pycache-remove
pycache-remove: ## Clean PyCache
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: dsstore-remove
dsstore-remove: ## Clean .DS_Store
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: mypycache-remove
mypycache-remove: ## Clean .mypy_cache
	find . | grep -E ".mypy_cache" | xargs rm -rf

.PHONY: ipynbcheckpoints-remove
ipynbcheckpoints-remove: ## Clean ipynb_checkpoints
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

.PHONY: pytestcache-remove
pytestcache-remove: ## Clean pytest_cache
	find . | grep -E ".pytest_cache" | xargs rm -rf

.PHONY: build-remove
build-remove: ## Clean Builds
	rm -rf build/
	rm -rf build_linux/
	rm -rf build_win/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

#-----------------------------------------------------------------------------------------
# HELP
#-----------------------------------------------------------------------------------------
.PHONY: help
help: ## Self-documented Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
