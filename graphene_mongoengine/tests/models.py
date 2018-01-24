from datetime import datetime
from mongoengine import (
    connect, Document, EmbeddedDocument
)
from mongoengine.fields import (
    DateTimeField, EmailField, EmbeddedDocumentField, ListField,
    MapField, ReferenceField, StringField
)

connect(host='mongodb://localhost:27017', alias='default')

class Editor(Document):

    meta = {'collection': 'test_editor'}
    name = StringField(max_length=16, required=True)


class Pet(Document):

    meta = {'collection': 'test_pet'}
    name = StringField(max_length=16, required=True)
    reporter_id = StringField()


class Article(EmbeddedDocument):

    meta = {'collection': 'test_article'}
    headline = StringField(required=True)
    pub_date = DateTimeField(default=datetime.now)
    editor = ReferenceField(Editor)
    reporter = ReferenceField('Reporter')



class Reporter(Document):
    meta = {'collection': 'test_repoter'}

    first_name = StringField(required=True)
    last_name = StringField(requred=True)
    email = EmailField()
    ariticles = ListField(EmbeddedDocumentField(Article))
    #custom_map = MapField(field=StringField())
    awards = ListField(StringField())

