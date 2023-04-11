import graphene
from graphene.relay import Node

from . import models
from . import types  # noqa: F401
from .models import ProfessorMetadata
from ..types_async import AsyncMongoengineObjectType


class PublisherAsyncNode(AsyncMongoengineObjectType):
    legal_name = graphene.String()
    bad_field = graphene.String()

    class Meta:
        model = models.Publisher
        only_fields = ("id", "name")
        interfaces = (Node,)


class ArticleAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Article
        interfaces = (Node,)


class EditorAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Editor
        interfaces = (Node,)


class EmbeddedArticleAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.EmbeddedArticle
        interfaces = (Node,)


class PlayerAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Player
        interfaces = (Node,)
        filter_fields = {"first_name": ["istartswith", "in"]}


class ReporterAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Reporter
        interfaces = (Node,)


class ParentAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Parent
        interfaces = (Node,)


class ChildAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Child
        interfaces = (Node,)


class ChildRegisteredBeforeAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredBefore
        interfaces = (Node,)


class ChildRegisteredAfterAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ChildRegisteredAfter
        interfaces = (Node,)


class ParentWithRelationshipAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ParentWithRelationship
        interfaces = (Node,)


class ProfessorMetadataAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = ProfessorMetadata
        interfaces = (graphene.Node,)


class ProfessorVectorAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ProfessorVector
        interfaces = (Node,)


class ErroneousModelAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.ErroneousModel
        interfaces = (Node,)


class BarAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Bar
        interfaces = (Node,)


class FooAsyncNode(AsyncMongoengineObjectType):
    class Meta:
        model = models.Foo
        interfaces = (Node,)
