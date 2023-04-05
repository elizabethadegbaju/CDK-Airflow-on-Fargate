# define the name of the virtual environment directory
VENV := .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
VENV_ACTIVATE=python3 -m venv $(VENV) && . $(VENV)/bin/activate
CDK = npx aws-cdk@2.70.0

# venv is a shortcut target
venv: $(VENV)/bin/activate

pip_update:
	$(VENV_ACTIVATE) && $(PIP) install --upgrade pip

install: pip_update venv
	pip install -r requirements.txt

test: venv
	pytest -o log_cli_level=INFO -W ignore::DeprecationWarning -s tests

lint: venv
	flake8 . --exclude=*.pyc,.venv/,.pytest_cache/,__pycache__/,website/,cdk.out --max-line-length 110

fmt: venv
	black .

deploy:
	$(CDK) deploy --require-approval never

destroy:
	$(CDK) destroy

watch:
	$(CDK) watch

clean:
	rm -rf .pytest_cache **/__pycache__ cdk.out


.PHONY: install test lint fmt synth clean
