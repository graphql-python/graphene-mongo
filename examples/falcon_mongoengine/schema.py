import graphene
from graphene_mongo.fields import MongoengineConnectionField
from .types import CategoryType, BookmarkType


class Query(graphene.ObjectType):
    categories = MongoengineConnectionField(CategoryType)
    bookmarks = MongoengineConnectionField(BookmarkType)


schema = graphene.Schema(query=Query, types=[CategoryType, BookmarkType])
