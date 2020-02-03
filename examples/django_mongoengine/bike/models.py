from mongoengine import Document
from mongoengine.fields import (
    FloatField,
    StringField,
    ListField,
    URLField,
    ObjectIdField,
)


class Shop(Document):
    meta = {"collection": "shop"}
    ID = ObjectIdField()
    name = StringField()
    address = StringField()
    website = URLField()


class Bike(Document):
    meta = {"collection": "bike"}
    ID = ObjectIdField()
    name = StringField()
    brand = StringField()
    year = StringField()
    size = ListField(StringField())
    wheel_size = FloatField()
    type = StringField()
