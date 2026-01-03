import sys

import graphene
import mongoengine

from graphene.types.json import JSONString
from graphene.utils.str_converters import to_camel_case
from mongoengine.base import get_document
from . import advanced_types
from .utils import (
    get_field_description,
    get_field_is_required,
    get_field_resolver,
    ExecutorEnum,
)
from .field_resolvers import (
    DynamicLazyFieldResolver,
    DynamicReferenceFieldResolver,
    ListFieldResolver,
    UnionFieldResolver,
)
from functools import singledispatch


class MongoEngineConversionError(Exception):
    pass


@singledispatch
def convert_mongoengine_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    raise MongoEngineConversionError(
        "Don't know how to convert the MongoEngine field %s (%s)" % (field, field.__class__)
    )


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.String(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.ID(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.IntField)
@convert_mongoengine_field.register(mongoengine.LongField)
@convert_mongoengine_field.register(mongoengine.SequenceField)
def convert_field_to_int(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Int(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Boolean(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Float(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.Decimal128Field)
@convert_mongoengine_field.register(mongoengine.DecimalField)
def convert_field_to_decimal(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Decimal(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_field_to_datetime(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.DateTime(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.DateField)
def convert_field_to_date(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Date(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_field_to_jsonstring(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return JSONString(
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.PointField)
def convert_point_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.PointFieldType,
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.PolygonField)
def convert_polygon_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.PolygonFieldType,
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.MultiPolygonField)
def convert_multipolygon_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.MultiPolygonFieldType,
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.FileField)
def convert_file_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.FileFieldType,
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.ListField)
@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentListField)
@convert_mongoengine_field.register(mongoengine.GeoPointField)
def convert_field_to_list(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    base_type = convert_mongoengine_field(field.field, registry=registry, executor=executor)
    if isinstance(base_type, graphene.Field):
        if isinstance(field.field, mongoengine.GenericReferenceField):
            return graphene.List(
                base_type._type,
                description=get_field_description(field, registry),
                required=get_field_is_required(field, registry),
                resolver=get_field_resolver(
                    default_sync_resolver=ListFieldResolver.reference_resolver(
                        field=field, registry=registry, executor=executor
                    ),
                    default_async_resolver=ListFieldResolver.reference_resolver_async(
                        field=field, registry=registry, executor=executor
                    ),
                    executor=executor,
                ),
            )
        return graphene.List(
            base_type._type,
            description=get_field_description(field, registry),
            required=get_field_is_required(field, registry),
        )
    if isinstance(base_type, (graphene.Dynamic)):
        base_type = base_type.get_type()
        if base_type is None:
            return
        base_type = base_type._type

    if graphene.is_node(base_type):
        return base_type._meta.connection_field_class(base_type)

    # Non-relationship field
    relations = (mongoengine.ReferenceField, mongoengine.EmbeddedDocumentField)
    if not isinstance(base_type, (graphene.List, graphene.NonNull)) and not isinstance(
        field.field, relations
    ):
        base_type = type(base_type)

    return graphene.List(
        base_type,
        description=get_field_description(field, registry),
        required=get_field_is_required(field, registry),
    )


@convert_mongoengine_field.register(mongoengine.GenericEmbeddedDocumentField)
@convert_mongoengine_field.register(mongoengine.GenericReferenceField)
def convert_field_to_union(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    _types = []
    for choice in field.choices:
        if isinstance(field, mongoengine.GenericReferenceField):
            _field = mongoengine.ReferenceField(get_document(choice))
        elif isinstance(field, mongoengine.GenericEmbeddedDocumentField):
            _field = mongoengine.EmbeddedDocumentField(choice)

        _field = convert_mongoengine_field(_field, registry, executor=executor)
        _type = _field.get_type()
        if _type:
            _types.append(_type.type)
        else:
            # TODO: Register type auto-matically here.
            pass

    if len(_types) == 0:
        return None

    field_name = field.db_field
    if field_name is None:
        # Get db_field name from parent mongo_field
        for db_field_name, _mongo_parent_field in field.owner_document._fields.items():
            if hasattr(_mongo_parent_field, "field") and _mongo_parent_field.field == field:
                field_name = db_field_name
                break

    name = to_camel_case(
        "{}_{}_union_type".format(
            field._owner_document.__name__,
            field_name,
        )
    )
    Meta = type("Meta", (object,), {"types": tuple(_types)})
    _union = type(name, (graphene.Union,), {"Meta": Meta})

    if isinstance(field, mongoengine.GenericReferenceField) or isinstance(
        field, mongoengine.GenericLazyReferenceField
    ):
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = get_field_is_required(field, registry)
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _union,
            resolver=get_field_resolver(
                field_resolver=field_resolver,
                default_sync_resolver=UnionFieldResolver.resolver(
                    field=field, registry=registry, executor=executor
                ),
                default_async_resolver=UnionFieldResolver.resolver_async(
                    field=field, registry=registry, executor=executor
                ),
                executor=executor,
            ),
            description=get_field_description(field, registry),
            required=required,
        )

    return graphene.Field(_union)


@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentField)
@convert_mongoengine_field.register(mongoengine.ReferenceField)
@convert_mongoengine_field.register(mongoengine.CachedReferenceField)
def convert_field_to_dynamic(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    model = field.document_type

    def dynamic_type():
        _type = registry.get_type_for_model(model, executor=executor)
        if not _type:
            return None
        if isinstance(field, mongoengine.EmbeddedDocumentField):
            return graphene.Field(
                _type,
                description=get_field_description(field, registry),
                required=get_field_is_required(field, registry),
            )
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = get_field_is_required(field, registry)
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _type,
            resolver=get_field_resolver(
                field_resolver=field_resolver,
                default_sync_resolver=DynamicReferenceFieldResolver.reference_resolver(
                    field=field, registry=registry, executor=executor
                ),
                default_async_resolver=DynamicReferenceFieldResolver.reference_resolver_async(
                    field=field, registry=registry, executor=executor
                ),
                executor=executor,
            ),
            description=get_field_description(field, registry),
            required=required,
        )

    return graphene.Dynamic(dynamic_type)


@convert_mongoengine_field.register(mongoengine.LazyReferenceField)
def convert_lazy_field_to_dynamic(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    model = field.document_type

    def dynamic_type():
        _type = registry.get_type_for_model(model, executor=executor)
        if not _type:
            return None
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = get_field_is_required(field, registry)
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function

        return graphene.Field(
            _type,
            resolver=get_field_resolver(
                field_resolver=field_resolver,
                default_sync_resolver=DynamicLazyFieldResolver.lazy_resolver(
                    field=field, registry=registry, executor=executor
                ),
                default_async_resolver=DynamicLazyFieldResolver.lazy_resolver_async(
                    field=field, registry=registry, executor=executor
                ),
                executor=executor,
            ),
            description=get_field_description(field, registry),
            required=required,
        )

    return graphene.Dynamic(dynamic_type)


if sys.version_info >= (3, 6):

    @convert_mongoengine_field.register(mongoengine.EnumField)
    def convert_field_to_enum(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
        if not registry.check_enum_already_exist(field._enum_cls):
            registry.register_enum(field._enum_cls)
        _type = registry.get_type_for_enum(field._enum_cls)
        return graphene.Field(
            _type,
            description=get_field_description(field, registry),
            required=get_field_is_required(field, registry),
        )
