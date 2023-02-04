from mongoengine import Document, CASCADE
from mongoengine.fields import StringField, ListField, ReferenceField


class Category(Document):
    meta = {"collection": "category"}
    name = StringField(max_length=140, required=True)
    color = StringField(max_length=7, required=True)


class Bookmark(Document):
    meta = {"collection": "bookmark"}
    name = StringField(required=True)
    url = StringField(required=True)
    category = ReferenceField("Category", reverse_delete_rule=CASCADE)
    tags = ListField(StringField(max_length=50))
