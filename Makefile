# build & publish

build:
	poetry build

publish-pip:
	poetry publish


# formatting

fmt-black:
	poetry run black beancount_bd/ tests/

# lint

lint:
	poetry run black --check beancount_bd/ tests/

# test

test:
	poetry run pytest tests/
