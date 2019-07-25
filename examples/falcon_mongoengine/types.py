import graphene
from graphene import relay
from graphene_mongo import MongoengineObjectType

from .models import Category, Bookmark


class CategoryType(MongoengineObjectType):
    class Meta:
        model = Category
        interfaces = (relay.Node,)


class BookmarkType(MongoengineObjectType):
    class Meta:
        model = Bookmark
        interfaces = (relay.Node,)
