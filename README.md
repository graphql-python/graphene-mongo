[![Build Status](https://travis-ci.org/graphql-python/graphene-mongo.svg?branch=master)](https://travis-ci.org/graphql-python/graphene-mongo) [![Coverage Status](https://coveralls.io/repos/github/graphql-python/graphene-mongo/badge.svg?branch=master)](https://coveralls.io/github/graphql-python/graphene-mongo?branch=master) [![Documentation Status](https://readthedocs.org/projects/graphene-mongo/badge/?version=latest)](http://graphene-mongo.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/graphene-mongo.svg)](https://badge.fury.io/py/graphene-mongo) [![PyPI pyversions](https://img.shields.io/pypi/pyversions/graphene-mongo.svg)](https://pypi.python.org/pypi/graphene-mongo/)

# Graphene-Mongo

A [Mongoengine](https://mongoengine-odm.readthedocs.io/) integration for [Graphene](http://graphene-python.org/).


## Installation

For instaling graphene-mongo, just run this command in your shell

```
pip install graphene-mongo
```

## Examples

Here is a simple Mongoengine model as `models.py`:

```python
from mongoengine import Document
from mongoengine.fields import StringField

class User(Document):
    meta = {'collection': 'user'}
    first_name = StringField(required=True)
    last_name = StringField(required=True)
```

To create a GraphQL schema for it you simply have to write the following:

```python
import graphene

from graphene_mongo import MongoengineObjectType

from .models import User as UserModel

class User(MongoengineObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    users = graphene.List(User)
    
    def resolve_users(self, info):
    	return list(UserModel.objects.all())

schema = graphene.Schema(query=Query)
```

Then you can simply query the schema:

```python
query = '''
    query {
        users {
            firstName,
            lastName
        }
    }
'''
result = schema.execute(query)
```

To learn more check out the following [examples](examples/):

* **Full example**: [Flask MongoEngine example](examples/flask_mongoengine)

## TODOs

- [ ] Examples
    - [x] Flask example
    - [ ] Django example
- [ ] Filtering & Paging
    - [x] Default filtering enabled with all model's attributes by equal comparison (requester: [git-albertomarin](https://github.com/git-albertomarin))
    - [x] Take first, or last n items (credit: [alexpantyukhin](https://github.com/alexpantyukhin))
    - [x] Filter by global id (requester: [bwalsh](https://github.com/bwalsh))
    - [ ] Advanced filtering
- [ ] Support more types
    - [x] Self-reference and list-of-self-reference relationship (requester: [mehdiym](https://github.com/mehdiym))
    - [x] ListField(EmbeddedDocumentField)
    - [ ] Others

## Contributing

After cloning this repo, ensure dependencies are installed by running:

```sh
pip install -r requirements.txt
```

After developing, the full test suite can be evaluated by running:

```sh
make test
```
