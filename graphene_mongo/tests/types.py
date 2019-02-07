import graphene
from graphene.relay import Node

from ..types import MongoengineObjectType
from .models import (
    Article, Editor, EmbeddedArticle, Player, Reporter,
    Parent, Child, ProfessorMetadata, ProfessorVector,
    ParentWithRelationship, ChildRegisteredBefore,
    ChildRegisteredAfter, CellTower,
    Publisher, ErroneousModel)


class PublisherType(MongoengineObjectType):

    class Meta:
        model = Publisher


class EditorType(MongoengineObjectType):

    class Meta:
        model = Editor


class ArticleType(MongoengineObjectType):

    class Meta:
        model = Article


class EmbeddedArticleType(MongoengineObjectType):

    class Meta:
        model = EmbeddedArticle


class PlayerType(MongoengineObjectType):

    class Meta:
        model = Player


class ReporterType(MongoengineObjectType):

    class Meta:
        model = Reporter


class ParentType(MongoengineObjectType):

    class Meta:
        model = Parent


class ChildType(MongoengineObjectType):

    class Meta:
        model = Child


class CellTowerType(MongoengineObjectType):

    class Meta:
        model = CellTower


class ProfessorMetadataType(MongoengineObjectType):

    class Meta:
        model = ProfessorMetadata


class ProfessorVectorType(MongoengineObjectType):

    class Meta:
        model = ProfessorVector


class PublisherNode(MongoengineObjectType):
    legal_name = graphene.String()
    bad_field = graphene.String()

    class Meta:
        model = Publisher
        only_fields = ('id', 'name')
        interfaces = (Node,)


class ArticleNode(MongoengineObjectType):

    class Meta:
        model = Article
        interfaces = (Node,)


class EditorNode(MongoengineObjectType):

    class Meta:
        model = Editor
        interfaces = (Node,)


class EmbeddedArticleNode(MongoengineObjectType):

    class Meta:
        model = EmbeddedArticle
        interfaces = (Node,)


class PlayerNode(MongoengineObjectType):

    class Meta:
        model = Player
        interfaces = (Node,)


class ReporterNode(MongoengineObjectType):

    class Meta:
        model = Reporter
        interfaces = (Node,)


class ParentNode(MongoengineObjectType):

    class Meta:
        model = Parent
        interfaces = (Node,)


class ChildNode(MongoengineObjectType):

    class Meta:
        model = Child
        interfaces = (Node,)


class ChildRegisteredBeforeNode(MongoengineObjectType):

    class Meta:
        model = ChildRegisteredBefore
        interfaces = (Node, )


class ParentWithRelationshipNode(MongoengineObjectType):

    class Meta:
        model = ParentWithRelationship
        interfaces = (Node, )


class ChildRegisteredAfterNode(MongoengineObjectType):

    class Meta:
        model = ChildRegisteredAfter
        interfaces = (Node, )


class ProfessorVectorNode(MongoengineObjectType):

    class Meta:
        model = ProfessorVector
        interfaces = (Node, )


class ErroneousModelNode(MongoengineObjectType):
    class Meta:
        model = ErroneousModel
        interfaces = (Node,)
