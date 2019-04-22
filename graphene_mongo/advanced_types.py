import graphene


__all__ = [
    'PointFieldType',
    'MultiPolygonFieldType'
]


def _resolve_type_coordinates(self, info):
    return self['coordinates']


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
