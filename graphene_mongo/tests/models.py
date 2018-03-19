from datetime import datetime
from mongoengine import (
    connect, Document, EmbeddedDocument
)
from mongoengine.fields import (
    DateTimeField, EmailField, EmbeddedDocumentField,
    EmbeddedDocumentListField, ListField,
    MapField, ReferenceField, StringField
)

connect('graphene-mongo-test', host='mongomock://localhost', alias='default')


class Editor(Document):

    meta = {'collection': 'test_editor'}
    id = StringField(primary_key=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)


class Pet(Document):

    meta = {'collection': 'test_pet'}
    name = StringField(max_length=16, required=True)
    reporter_id = StringField()


class Article(Document):

    meta = {'collection': 'test_article'}
    headline = StringField(required=True)
    pub_date = DateTimeField(default=datetime.now)
    editor = ReferenceField(Editor)
    reporter = ReferenceField('Reporter')


class EmbeddedArticle(EmbeddedDocument):

    meta = {'collection': 'test_embedded_article'}
    headline = StringField(required=True)
    pub_date = DateTimeField(default=datetime.now)
    editor = ReferenceField(Editor)
    reporter = ReferenceField('Reporter')


class Reporter(Document):
    meta = {'collection': 'test_repoter'}

    id = StringField(primary_key=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField()
    articles = ListField(ReferenceField(Article))
    embedded_articles = ListField(EmbeddedDocumentField(EmbeddedArticle))
    embedded_list_articles = EmbeddedDocumentListField(EmbeddedArticle)
    # FIXME
    # custom_map = MapField(field=StringField())
    awards = ListField(StringField())


class Player(Document):
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    opponent = ReferenceField('Player')
    players = ListField(ReferenceField('Player'))
    articles = ListField(ReferenceField('Article'))
    embedded_list_articles = EmbeddedDocumentListField(EmbeddedArticle)

