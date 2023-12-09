from . import models
from ..types import (
    MongoengineObjectType,
    MongoengineInterfaceType,
    MongoengineInputType,
)
from graphene.types.union import Union


class PublisherType(MongoengineObjectType):
    class Meta:
        model = models.Publisher


class EditorType(MongoengineObjectType):
    class Meta:
        model = models.Editor


class ArticleType(MongoengineObjectType):
    class Meta:
        model = models.Article


class EmbeddedArticleType(MongoengineObjectType):
    class Meta:
        model = models.EmbeddedArticle


class PlayerType(MongoengineObjectType):
    class Meta:
        model = models.Player


class ReporterType(MongoengineObjectType):
    class Meta:
        model = models.Reporter


class ParentType(MongoengineObjectType):
    class Meta:
        model = models.Parent


class ParentInterface(MongoengineInterfaceType):
    class Meta:
        model = models.Parent
        exclude_fields = ["loc"]


class ChildType(MongoengineObjectType):
    class Meta:
        model = models.Child
        interfaces = (ParentInterface,)


class AnotherChildType(MongoengineObjectType):
    class Meta:
        model = models.AnotherChild
        interfaces = (ParentInterface,)


class ChildUnionType(Union):
    class Meta:
        types = (ChildType, AnotherChildType)
        interfaces = (ParentInterface,)


class CellTowerType(MongoengineObjectType):
    class Meta:
        model = models.CellTower


class ProfessorMetadataType(MongoengineObjectType):
    class Meta:
        model = models.ProfessorMetadata


class ProfessorVectorType(MongoengineObjectType):
    class Meta:
        model = models.ProfessorVector


class ArticleInput(MongoengineInputType):
    class Meta:
        model = models.Article
        only_fields = ["headline"]


class EditorInput(MongoengineInputType):
    class Meta:
        model = models.Editor
        only_fields = ["first_name", "last_name"]
        # allow providing only one of those ! Even None...
        non_required_fields = ["first_name", "last_name"]
