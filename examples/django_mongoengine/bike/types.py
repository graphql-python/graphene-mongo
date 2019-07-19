from graphene import relay
from graphene_mongo import MongoengineObjectType
from .models import Bike


class BikeType(MongoengineObjectType):
    class Meta:
        model = Bike
        interfaces = (relay.Node,)
