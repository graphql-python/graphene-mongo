Mongoengine + Flask Tutorial
==============================

Graphene comes with builtin support to Mongoengine, which makes quite
easy to operate with your current models.

Note: The code in this tutorial is pulled from the `Flask Mongoengine
example
app <https://github.com/abawchen/graphene-mongo/tree/master/examples/flask_mongoengine>`__.

Setup the Project
-----------------

.. code:: bash

    # Create the project directory
    mkdir flask_graphene_mongo
    cd flask_graphene_mongo

    # [Optional but suggested] Create a virtualenv to isolate our package dependencies locally
    virtualenv env
    source env/bin/activate

    # Install required packages
    pip install Flask
    pip install Flask-GraphQL
    pip install graphene-mongo

    # Install mongomock or you have to run a real mongo server instance somewhere.
    pip install mongomock

Defining our models
-------------------

Let's get start with following models:

.. code:: python

    # flask_graphene_mongo/models.py
    from datetime import datetime
    from mongoengine import Document
    from mongoengine.fields import (
        DateTimeField, ReferenceField, StringField,
    )


    class Department(Document):
        meta = {'collection': 'department'}
        name = StringField()


    class Role(Document):
        meta = {'collection': 'role'}
        name = StringField()


    class Employee(Document):
        meta = {'collection': 'employee'}
        name = StringField()
        hired_on = DateTimeField(default=datetime.now)
        department = ReferenceField(Department)
        role = ReferenceField(Role)

Schema
------

Here I assume you guys have the basic knowledge of how schema works in GraphQL, that I define the *root type*  as the `Query` class below with the ability to list all employees.

.. code:: python

    # flask_graphene_mongo/schema.py
    import graphene
    from graphene.relay import Node
    from graphene_mongo import MongoengineConnectionField, MongoengineObjectType
    from models import Department as DepartmentModel
    from models import Employee as EmployeeModel
    from models import Role as RoleModel

    class Department(MongoengineObjectType):

        class Meta:
            model = DepartmentModel
            interfaces = (Node,)


    class Role(MongoengineObjectType):

        class Meta:
            model = RoleModel
            interfaces = (Node,)


    class Employee(MongoengineObjectType):

        class Meta:
            model = EmployeeModel
            interfaces = (Node,)


    class Query(graphene.ObjectType):
        node = Node.Field()
        all_employees = MongoengineConnectionField(Employee)
        all_role = MongoengineConnectionField(Role)
        role = graphene.Field(Role)

    schema = graphene.Schema(query=Query, types=[Department, Employee, Role])


Creating some data
------------------

By putting some data to make this demo can run directly:

.. code:: python

    # flask_graphene_mongo/database.py
    from mongoengine import connect

    from models import Department, Employee, Role

    # You can connect to a real mongo server instance by your own.
    connect('graphene-mongo-example', host='mongomock://localhost', alias='default')


    def init_db():
        # Create the fixtures
        engineering = Department(name='Engineering')
        engineering.save()

        hr = Department(name='Human Resources')
        hr.save()

        manager = Role(name='manager')
        manager.save()

        engineer = Role(name='engineer')
        engineer.save()

        peter = Employee(name='Peter', department=engineering, role=engineer)
        peter.save()

        roy = Employee(name='Roy', department=engineering, role=engineer)
        roy.save()

        tracy = Employee(name='Tracy', department=hr, role=manager)
        tracy.save()

Creating GraphQL and GraphiQL views in Flask
--------------------------------------------

There is only one URL from which GraphQL is accessed, and we take the advantage of ``Flask-GraphQL`` to generate the GraphQL interface for easily accessed by a browser:

.. code:: python

    # flask_graphene_mongo/app.py
    from database import init_db
    from flask import Flask
    from flask_graphql import GraphQLView
    from schema import schema

    app = Flask(__name__)
    app.debug = True

    default_query = '''
    {
      allEmployees {
        edges {
          node {
            id,
            name,
            department {
              id,
              name
            },
            role {
              id,
              name
            }
          }
        }
      }
    }'''.strip()

    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
    )

    if __name__ == '__main__':
        init_db()
        app.run()

Testing
-------

We are ready to launch the server!

.. code:: bash

    $ python app.py
        * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Then go to `http://localhost:5000/graphql <http://localhost:5000/graphql>`__ to test your first query.

