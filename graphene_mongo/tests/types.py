from graphene.relay import Node

from ..types import MongoengineObjectType
from .models import (
    Article, Editor, EmbeddedArticle, Player, Reporter,
    Parent, Child, ProfessorMetadata, ProfessorVector,
    ParentWithRelationship, ChildRegisteredBefore,
    ChildRegisteredAfter
)


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


class ProfessorMetadataType(MongoengineObjectType):

    class Meta:
        model = ProfessorMetadata


class ProfessorVectorType(MongoengineObjectType):

    class Meta:
        model = ProfessorVector


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
