
Example Falcon+MongoEngine Project
================================

This example project demos integration between Graphene, Falcon and MongoEngine.

Getting started
---------------

First you'll need to get the source of the project. Do this by cloning the
whole Graphene repository:

```bash
# Get the example project code
git clone git@github.com:abawchen/graphene-mongo.git
cd graphene-mongo/examples/falcon_mongoengine
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

Setup a mongodb connection and create a database.
See the mongoengine connection details in the *app.py* file

Start the server:

On windows:
```
waitress-serve --port=9000 falcon_mongoengine.app:app
```

On Linux:
```
gunicorn -b 0.0.0.0:9000 falcon_mongoengine.app:app
```

Now head on over to
[http://127.0.0.1:9000/graphql?query=](http://127.0.0.1:9000/graphql?query=)
and run some queries!

Example:

```
http://127.0.0.1:9000/graphql?query=query
    {
        categories(first: 1, name: "Travel")
         {
            edges { node { name color } }
          }
    }
```

```
http://127.0.0.1:9000/graphql?query=query
    { 
        bookmarks(first: 10) 
        { 
            pageInfo { startCursor endCursor hasNextPage hasPreviousPage }
            edges { 
                node { name url category { name color } tags }
                   }
        }
    }
```

For tests run:

```python
pytest -v
```
