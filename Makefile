clean:
	@rm -f .coverage 2> /dev/null
	@rm -rf .eggs 2> /dev/null
	@rm -rf .cache 2> /dev/null
	@rm -rf ./graphene_mongo/.cache 2> /dev/null
	@rm -rf build 2> /dev/null
	@rm -rf dist 2> /dev/null
	@rm -rf graphene_mongo.egg-info 2> /dev/null
	@find . -name "*.pyc" -delete
	@find . -name "*.swp" -delete
	@find . -name "__pycache__" -delete

lint:
	@flake8 graphene_mongo

test: clean lint
	pytest graphene_mongo/tests --cov=graphene_mongo --cov-report=html --cov-report=term

register-pypitest:
	#python setup.py register -r pypitest

deploy-pypitest: clean
	poetry build
	#poetry publish --repository testpypi
	twine upload --repository testpypi dist/*

register:
	#python setup.py register -r pypi

deploy: clean
	poetry build
	twine upload dist/*
	#poetry publish

