import graphene
from graphene.relay import Node

from . import models
from . import types  # noqa: F401
from ..types_async import AsyncMongoengineObjectType


class PublisherNode(AsyncMongoengineObjectType):
    legal_name = graphene.String()
    bad_field = graphene.String()

    class Meta:
        model = models.Publisher
        only_fields = ("id", "name")
        interfaces = (Node,)


class ArticleNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Article
        interfaces = (Node,)


class EditorNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Editor
        interfaces = (Node,)


class EmbeddedArticleNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.EmbeddedArticle
        interfaces = (Node,)


class PlayerNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Player
        interfaces = (Node,)
        filter_fields = {"first_name": ["istartswith", "in"]}


class ReporterNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Reporter
        interfaces = (Node,)


class ReporterNodeAsync(AsyncMongoengineObjectType):
    class Meta:
        model = models.Reporter
        interfaces = (Node,)


class ParentNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Parent
        interfaces = (Node,)


class ChildNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Child
        interfaces = (Node,)


class ChildRegisteredBeforeNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredBefore
        interfaces = (Node,)


class ParentWithRelationshipNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ParentWithRelationship
        interfaces = (Node,)


class ChildRegisteredAfterNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredAfter
        interfaces = (Node,)


class ProfessorVectorNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ProfessorVector
        interfaces = (Node,)


class ErroneousModelNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ErroneousModel
        interfaces = (Node,)


class BarNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Bar
        interfaces = (Node,)


class FooNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Foo
        interfaces = (Node,)
