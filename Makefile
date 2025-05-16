.PHONY: test
test:
	python attest.py
	python dateutil.py
	python keys.py
	python guestwaiver.py
	python memberwaiver.py
	mypy *.py

