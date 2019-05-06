import base64
import graphene


def _resolve_type_coordinates(self, info):
    return self['coordinates']


def _resolve_fs_field(field, name, default_value=None):
    v = getattr(field.instance, field.key)
    return getattr(v, name, default_value)


def _resolve_content_type(self, info):
    return _resolve_fs_field(self, 'content_type')


def _resolve_md5(self, info):
    return _resolve_fs_field(self, 'md5')


def _resolve_chunk_size(self, info):
    return _resolve_fs_field(self, 'chunk_size', 0)


def _resolve_length(self, info):
    return _resolve_fs_field(self, 'length', 0)


def _resolve_data(self, info):
    v = getattr(self.instance, self.key)
    data = v.read()
    if data is not None:
        return base64.b64encode(data)
    return None


class FileFieldType(graphene.ObjectType):

    content_type = graphene.String(resolver=_resolve_content_type)
    md5 = graphene.String(resolver=_resolve_md5)
    chunk_size = graphene.Int(resolver=_resolve_chunk_size)
    length = graphene.Int(resolver=_resolve_length)
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
