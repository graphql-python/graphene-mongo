from datetime import datetime
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    DateTimeField,
    EmbeddedDocumentField,
    ListField,
    ReferenceField,
    StringField,
)


class Department(Document):

    meta = {"collection": "department"}
    name = StringField()


class Role(Document):

    meta = {"collection": "role"}
    name = StringField()


class Task(EmbeddedDocument):

    name = StringField()
    deadline = DateTimeField(default=datetime.now)


class Employee(Document):

    meta = {"collection": "employee"}
    name = StringField()
    hired_on = DateTimeField(default=datetime.now)
    department = ReferenceField(Department)
    roles = ListField(ReferenceField(Role))
    leader = ReferenceField("Employee")
    tasks = ListField(EmbeddedDocumentField(Task))
