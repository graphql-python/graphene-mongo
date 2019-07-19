from mongoengine import Document
from mongoengine.fields import FloatField, StringField, ListField


class Bike(Document):
    meta = {'collection': 'bike'}
    name = StringField()
    brand = StringField()
    year = StringField()
    size = ListField(StringField())
    wheel_size = FloatField()
    type = StringField()
