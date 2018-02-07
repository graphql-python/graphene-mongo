from graphene.relay import Node

from .models import Article, Editor, Reporter
from ..types import MongoengineObjectType


class EditorType(MongoengineObjectType):
    class Meta:
        model = Editor


class ArticleType(MongoengineObjectType):
    class Meta:
        model = Article

class ReporterType(MongoengineObjectType):
    class Meta:
        model = Reporter


class ArticleNode(MongoengineObjectType):

    class Meta:
        model = Article
        interfaces = (Node,)

class EditorNode(MongoengineObjectType):

    class Meta:
        model = Editor
        interfaces = (Node,)


class ReporterNode(MongoengineObjectType):

    class Meta:
        model = Reporter
        interfaces = (Node,)

