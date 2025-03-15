run:
	@clear;
	@python app.py

tests:
	@clear;
	@python -m pytest -v

verbose-tests:
	@clear;
	@python -m pytest -s -v
