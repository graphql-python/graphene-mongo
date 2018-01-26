# Graphene-Mongo

A [Mongoengine](https://mongoengine-odm.readthedocs.io/) integration for [Graphene](http://graphene-python.org/).


## Installation

For instaling graphene, just run this command in your shell

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

## TODOs

- [ ] Examples
- [ ] Support List(EmbeddedDocument)
- [ ] Paging
- [ ] Filtering

## Contributing

After cloning this repo, ensure dependencies are installed by running:

```sh
python setup.py install
```

After developing, the full test suite can be evaluated by running:

```sh
python setup.py test # Use --pytest-args="-v -s" for verbose mode
```
