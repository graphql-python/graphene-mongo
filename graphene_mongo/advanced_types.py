import graphene

from mongoengine import Document
from mongoengine.fields import (
    IntField,
    StringField,
)

from .types import MongoengineObjectType

__all__ = [
    'PointFieldType',
    'MultiPolygonFieldType'
]


def _resolve_type_coordinates(self, info):
    return self['coordinates']


class FsFile(Document):

    meta = {'collection': 'fs.files'}
    content_type = StringField(name='contentType')
    chunk_size = IntField(name='chunkSize')
    length = IntField()
    md5 = StringField()


class FsFileType(MongoengineObjectType):

    class Meta:
        model = FsFile


class _TypeField(graphene.ObjectType):

    type = graphene.String()

    def resolve_type(self, info):
        return self['type']


class PointFieldType(_TypeField):

    coordinates = graphene.List(
        graphene.Float, resolver=_resolve_type_coordinates)


class PolygonFieldType(_TypeField):

    coordinates = graphene.List(
        graphene.List(
            graphene.List(graphene.Float)),
        resolver=_resolve_type_coordinates
    )


class MultiPolygonFieldType(_TypeField):

    coordinates = graphene.List(
        graphene.List(
            graphene.List(
                graphene.List(graphene.Float))),
        resolver=_resolve_type_coordinates)
