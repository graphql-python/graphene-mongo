import falcon
from mongoengine import connect
from .api import GraphQLResource, HelloWorldResource

connect("bookmarks_db", host="127.0.0.1", port=27017)
app = application = falcon.API()

helloWorld = HelloWorldResource()
graphQL = GraphQLResource()

app.add_route("/", helloWorld)
app.add_route("/graphql", graphQL)
