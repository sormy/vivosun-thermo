# Vivosun Thermo Development

## Workspace

Install dependencies and create venv:

```sh
brew install python
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt -r requirements.dev.txt -r requirements.proto.txt
.venv/bin/pip3 install -e .
```

Run CLI:

```sh
.venv/bin/vivosun-thermo ...
```

Run prototype:

```sh
PYTHONPATH=src .venv/bin/python3 examples/prototype.py
```

Run tests on venv python:

```sh
.venv/bin/pytest
```

Check coverage:

```sh
open coverage/index.html
```

Run integration tests:

```sh
brew install tox python@3.10 python@3.11 python@3.12 python@3.13
tox
```

## Debugging

Enable Bleak logs:

```sh
BLEAK_LOGGING=1 vivosun-thermo ...
```

## Publishing

```sh
# install locally
.venv/bin/pip3 install -e .
# test using cli
.venv/bin/vivosun-thermo --help
# clean
rm -rf dist
# test
tox
# build
.venv/bin/python3 -m build
# view what is included into wheel
unzip -l dist/*.whl
# check wheel
.venv/bin/twine check dist/*.whl
# upload to pypi
.venv/bin/twine upload --repository pypi dist/*
```
