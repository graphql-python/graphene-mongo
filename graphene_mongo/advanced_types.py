import base64
import graphene


class FileFieldType(graphene.ObjectType):

    content_type = graphene.String()
    md5 = graphene.String()
    chunk_size = graphene.Int()
    length = graphene.Int()
    data = graphene.String()

    @classmethod
    def _resolve_fs_field(cls, field, name, default_value=None):
        v = getattr(field.instance, field.key)
        return getattr(v, name, default_value)

    def resolve_content_type(self, info):
        return FileFieldType._resolve_fs_field(self, "content_type")

    def resolve_md5(self, info):
        return FileFieldType._resolve_fs_field(self, "md5")

    def resolve_chunk_size(self, info):
        return FileFieldType._resolve_fs_field(self, "chunk_size", 0)

    def resolve_length(self, info):
        return FileFieldType._resolve_fs_field(self, "length", 0)

    def resolve_data(self, info):
        v = getattr(self.instance, self.key)
        data = v.read()
        if data is not None:
            return base64.b64encode(data)
        return None


class _CoordinatesTypeField(graphene.ObjectType):

    type = graphene.String()

    def resolve_type(self, info):
        return self["type"]

    def resolve_coordinates(self, info):
        return self["coordinates"]


class PointFieldType(_CoordinatesTypeField):

    coordinates = graphene.List(graphene.Float)


class PolygonFieldType(_CoordinatesTypeField):

    coordinates = graphene.List(graphene.List(graphene.List(graphene.Float)))


class MultiPolygonFieldType(_CoordinatesTypeField):

    coordinates = graphene.List(
        graphene.List(graphene.List(graphene.List(graphene.Float)))
    )
