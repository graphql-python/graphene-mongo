from . import models
from ..types import MongoengineObjectType


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


class ChildType(MongoengineObjectType):
    class Meta:
        model = models.Child


class CellTowerType(MongoengineObjectType):
    class Meta:
        model = models.CellTower


class ProfessorMetadataType(MongoengineObjectType):
    class Meta:
        model = models.ProfessorMetadata


class ProfessorVectorType(MongoengineObjectType):
    class Meta:
        model = models.ProfessorVector
