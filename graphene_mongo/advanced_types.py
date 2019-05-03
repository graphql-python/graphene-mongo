import base64
import mongoengine
import graphene

from .types import MongoengineObjectType


def _resolve_type_coordinates(self, info):
    return self['coordinates']


def _resolve_data(self, info):
    v = getattr(self.instance, self.key)
    data = v.read()
    return base64.b64encode(data)


class FsFile(mongoengine.Document):

    # TODO: Need to take care collection name instead of hard-code
    meta = {'collection': 'fs.files'}
    content_type = mongoengine.StringField(name='contentType')
    chunk_size = mongoengine.IntField(name='chunkSize')
    length = mongoengine.IntField()
    md5 = mongoengine.StringField()


class FsFileType(MongoengineObjectType):

    class Meta:
        model = FsFile

    data = graphene.String(resolver=_resolve_data)


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
