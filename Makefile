clean:
	@rm -f .coverage 2> /dev/null
	@rm -rf .eggs 2> /dev/null
	@rm -rf .cache 2> /dev/null
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete

register-pypitest:
	python setup.py register -r pypitest

deploy-pypitest:
	python setup.py sdist upload -r pypitest

register:
	python setup.py register -r pypi

deploy:
	python setup.py sdist upload -r pypi

