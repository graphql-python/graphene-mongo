from graphene import (ID, Boolean, Dynamic, Enum, Field, Float, Int, List,
                      NonNull, String, UUID)
from graphene.types.datetime import DateTime, Time
from graphene.types.json import JSONString
from graphene.utils.str_converters import to_camel_case, to_const
from graphql import assert_valid_name

import mongoengine

from .utils import import_single_dispatch

singledispatch = import_single_dispatch()


@singledispatch
def convert_mongoengine_field(field, registry=None):
    raise Exception(
        "Don't know how to convert the MongoEngine field %s (%s)" %
        (field, field.__class__))


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None):
    return String(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None):
    return ID(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.IntField)
def convert_field_to_int(field, registry=None):
    return Int(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return NonNull(Boolean, description=field.db_field)


@convert_mongoengine_field.register(mongoengine.DecimalField)
@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None):
    return Float(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_date_to_string(field, registry=None):
    return DateTime(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_dict_to_jsonstring(field, registry=None):
    return JSONString(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_date_to_string(field, registry=None):
    return String(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.ListField)
def convert_postgres_array_to_list(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
    if isinstance(base_type, (Dynamic)):
        base_type = base_type.get_type()._type
    if not isinstance(base_type, (List, NonNull)):
        base_type = type(base_type)
    return List(base_type, description=field.db_field, required=not field.null)

