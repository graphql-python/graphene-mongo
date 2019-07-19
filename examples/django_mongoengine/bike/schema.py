import graphene
from graphene.relay import Node
from graphene_mongo.fields import MongoengineConnectionField
from .types import BikeType


class Query(graphene.ObjectType):
    node = Node.Field()
    bikes = MongoengineConnectionField(BikeType)


schema = graphene.Schema(query=Query, types=[BikeType, ])
