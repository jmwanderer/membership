.PHONY: test
test:
	python dateutil.py
	python keys.py
	python docs.py
	mypy *.py

