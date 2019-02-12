from graphene import (
    ID,
    Boolean,
    DateTime,
    Dynamic,
    Field,
    Float,
    Int,
    List,
    NonNull,
    String,
    is_node
)
from graphene.types.json import JSONString

import mongoengine

from .advanced_types import PointFieldType, MultiPolygonFieldType
from .utils import import_single_dispatch, get_field_description

singledispatch = import_single_dispatch()


class MongoEngineConversionError(Exception):
    pass


@singledispatch
def convert_mongoengine_field(field, registry=None):
    raise MongoEngineConversionError(
        "Don't know how to convert the MongoEngine field %s (%s)" %
        (field, field.__class__))


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None):
    return String(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None):
    return ID(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.IntField)
@convert_mongoengine_field.register(mongoengine.LongField)
def convert_field_to_int(field, registry=None):
    return Int(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return Boolean(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.DecimalField)
@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None):
    return Float(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_dict_to_jsonstring(field, registry=None):
    return JSONString(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.PointField)
def convert_point_to_field(field, register=None):
    return Field(PointFieldType)


@convert_mongoengine_field.register(mongoengine.MultiPolygonField)
def convert_multipolygon_to_field(field, register=None):
    return Field(MultiPolygonFieldType)


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_field_to_datetime(field, registry=None):
    return DateTime(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.ListField)
@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentListField)
def convert_field_to_list(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
    if isinstance(base_type, (Dynamic)):
        base_type = base_type.get_type()
        if base_type is None:
            return
        base_type = base_type._type

    if is_node(base_type):
        return base_type._meta.connection_field_class(base_type)

    # Non-relationship field
    relations = (mongoengine.ReferenceField, mongoengine.EmbeddedDocumentField)
    if not isinstance(base_type, (List, NonNull)) \
            and not isinstance(field.field, relations):
        base_type = type(base_type)

    return List(base_type, description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentField)
@convert_mongoengine_field.register(mongoengine.ReferenceField)
def convert_field_to_dynamic(field, registry=None):
    model = field.document_type

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        return Field(_type, description=get_field_description(field, registry))

    return Dynamic(dynamic_type)


@convert_mongoengine_field.register(mongoengine.LazyReferenceField)
def convert_lazy_field_to_dynamic(field, registry=None):
    model = field.document_type

    def lazy_resolver(root, *args, **kwargs):
        if getattr(root, field.name or field.db_name):
            return getattr(root, field.name or field.db_name).fetch()

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        return Field(_type, resolver=lazy_resolver, description=get_field_description(field, registry))

    return Dynamic(dynamic_type)
