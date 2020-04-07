.PHONY: tests
tests:
	pytest -x tests

.PHONY: coverage
coverage:
	pytest -x --cov=pnpbot --cov-report html tests
