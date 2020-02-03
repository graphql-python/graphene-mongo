import graphene
from graphene.relay import Node

from . import models
from . import types  # noqa: F401
from ..types import MongoengineObjectType


class PublisherNode(MongoengineObjectType):
    legal_name = graphene.String()
    bad_field = graphene.String()

    class Meta:
        model = models.Publisher
        only_fields = ("id", "name")
        interfaces = (Node,)


class ArticleNode(MongoengineObjectType):
    class Meta:
        model = models.Article
        interfaces = (Node,)


class EditorNode(MongoengineObjectType):
    class Meta:
        model = models.Editor
        interfaces = (Node,)


class EmbeddedArticleNode(MongoengineObjectType):
    class Meta:
        model = models.EmbeddedArticle
        interfaces = (Node,)


class PlayerNode(MongoengineObjectType):
    class Meta:
        model = models.Player
        interfaces = (Node,)
        filter_fields = {"first_name": ["istartswith", "in"]}


class ReporterNode(MongoengineObjectType):
    class Meta:
        model = models.Reporter
        interfaces = (Node,)


class ParentNode(MongoengineObjectType):
    class Meta:
        model = models.Parent
        interfaces = (Node,)


class ChildNode(MongoengineObjectType):
    class Meta:
        model = models.Child
        interfaces = (Node,)


class ChildRegisteredBeforeNode(MongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredBefore
        interfaces = (Node,)


class ParentWithRelationshipNode(MongoengineObjectType):
    class Meta:
        model = models.ParentWithRelationship
        interfaces = (Node,)


class ChildRegisteredAfterNode(MongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredAfter
        interfaces = (Node,)


class ProfessorVectorNode(MongoengineObjectType):
    class Meta:
        model = models.ProfessorVector
        interfaces = (Node,)


class ErroneousModelNode(MongoengineObjectType):
    class Meta:
        model = models.ErroneousModel
        interfaces = (Node,)


class BarNode(MongoengineObjectType):
    class Meta:
        model = models.Bar
        interfaces = (Node,)


class FooNode(MongoengineObjectType):
    class Meta:
        model = models.Foo
        interfaces = (Node,)
