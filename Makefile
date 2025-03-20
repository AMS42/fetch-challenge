run:
	@clear;
	@python app.py

debug:
	@clear;
	@python app.py --debug

docker:
	@clear;
	@docker build --tag fetch-challenge-app .;
	@docker run --name fetch-challenge-app --rm -d -p 8080:5000 fetch-challenge-app;

tests:
	@clear;
	@python -m pytest -v

verbose-tests:
	@clear;
	@python -m pytest -s -v
