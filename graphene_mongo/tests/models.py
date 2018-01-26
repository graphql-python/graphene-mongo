from datetime import datetime
from mongoengine import (
    connect, Document, EmbeddedDocument
)
from mongoengine.fields import (
    DateTimeField, EmailField, EmbeddedDocumentField, ListField,
    MapField, ReferenceField, StringField
)

connect('graphene-mongo-test', host='mongomock://localhost', alias='default')


class Editor(Document):

    meta = {'collection': 'test_editor'}
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

    first_name = StringField(required=True)
    last_name = StringField(requred=True)
    email = EmailField()
    articles = ListField(ReferenceField(Article))
    # FIXME
    # embedded_articles = ListField(EmbeddedDocumentField(EmbeddedArticle))
    # FIXME
    # custom_map = MapField(field=StringField())
    awards = ListField(StringField())

