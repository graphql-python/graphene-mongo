
Example Django+MongoEngine Project
================================

This example project demos integration between Graphene, Django and MongoEngine.

Getting started
---------------

First you'll need to get the source of the project. Do this by cloning the
whole Graphene repository:

```bash
# Get the example project code
git clone git@github.com:abawchen/graphene-mongo.git
cd graphene-mongo/examples/django_mongoengine
```

Create a virtual environment.

```bash
# Create a virtualenv in which we can install the dependencies
virtualenv env
source env/bin/activate
```

Now we can install our dependencies:

```bash
pip install -r requirements.txt
```

Run the following command:

```python
python manage.py migrate
```

Setup a mongodb connection and create a database.
See the mongoengine connection details in the *settings.py* file

Start the server:

```python
python manage.py runserver
```

Now head on over to
[http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql)
and run some queries!

For tests run:

```python
pytest -v
```
