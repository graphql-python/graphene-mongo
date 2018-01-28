from datetime import datetime
from mongoengine import Document
from mongoengine.fields import (
    DateTimeField, ReferenceField, StringField,
)


class Department(Document):
    meta = {'collection': 'department'}
    name = StringField()


class Role(Document):
    meta = {'collection': 'role'}
    name = StringField()


class Employee(Document):
    meta = {'collection': 'employee'}
    name = StringField()
    hired_on = DateTimeField(default=datetime.now)
    department = ReferenceField(Department)
    role = ReferenceField(Role)

