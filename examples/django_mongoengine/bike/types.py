from graphene import relay
from graphene_mongo import MongoengineObjectType
from .models import Bike, Shop


class BikeType(MongoengineObjectType):
    class Meta:
        model = Bike
        interfaces = (relay.Node,)


class ShopType(MongoengineObjectType):
    class Meta:
        model = Shop
