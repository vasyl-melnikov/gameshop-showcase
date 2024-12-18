black ./
isort ./
flake8 ./
mypy --exclude=venv --exclude=app/db/migration ./