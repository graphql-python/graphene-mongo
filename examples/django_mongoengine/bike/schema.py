import graphene
from graphene.relay import Node
from graphene_mongo.fields import MongoengineConnectionField
from .models import Shop
from .types import BikeType, ShopType


class Query(graphene.ObjectType):
    node = Node.Field()
    bikes = MongoengineConnectionField(BikeType)
    shop_list = graphene.List(ShopType)

    def resolve_shop_list(self, info):
        return Shop.objects.all()


schema = graphene.Schema(query=Query, types=[BikeType, ShopType])
