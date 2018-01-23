clean:
	@rm -f .coverage 2> /dev/null
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete

