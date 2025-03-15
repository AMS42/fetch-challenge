run:
	@clear;
	@python app.py

test:
	@clear;
	@python -m pytest -v

verbose-test:
	@clear;
	@python -m pytest -s -v
