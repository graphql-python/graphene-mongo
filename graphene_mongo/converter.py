import asyncio
import sys

import graphene
import mongoengine

from graphene.types.json import JSONString
from graphene.utils.str_converters import to_snake_case, to_camel_case
from mongoengine.base import get_document, LazyReference
from . import advanced_types
from .utils import (
    get_field_description,
    get_query_fields,
    ExecutorEnum,
    sync_to_async,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.ID(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.IntField)
@convert_mongoengine_field.register(mongoengine.LongField)
@convert_mongoengine_field.register(mongoengine.SequenceField)
def convert_field_to_int(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Int(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Boolean(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Float(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.Decimal128Field)
@convert_mongoengine_field.register(mongoengine.DecimalField)
def convert_field_to_decimal(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Decimal(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_field_to_datetime(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.DateTime(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DateField)
def convert_field_to_date(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Date(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_field_to_jsonstring(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return JSONString(description=get_field_description(field, registry), required=field.required)


@convert_mongoengine_field.register(mongoengine.PointField)
def convert_point_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.PointFieldType,
        description=get_field_description(field, registry),
        required=field.required,
    )


@convert_mongoengine_field.register(mongoengine.PolygonField)
def convert_polygon_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.PolygonFieldType,
        description=get_field_description(field, registry),
        required=field.required,
    )


@convert_mongoengine_field.register(mongoengine.MultiPolygonField)
def convert_multipolygon_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.MultiPolygonFieldType,
        description=get_field_description(field, registry),
        required=field.required,
    )


@convert_mongoengine_field.register(mongoengine.FileField)
def convert_file_to_field(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    return graphene.Field(
        advanced_types.FileFieldType,
        description=get_field_description(field, registry),
        required=field.required,
    )


@convert_mongoengine_field.register(mongoengine.ListField)
@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentListField)
@convert_mongoengine_field.register(mongoengine.GeoPointField)
def convert_field_to_list(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    base_type = convert_mongoengine_field(field.field, registry=registry, executor=executor)
    if isinstance(base_type, graphene.Field):
        if isinstance(field.field, mongoengine.GenericReferenceField):

            def get_reference_objects(*args, **kwargs):
                document = get_document(args[0][0])
                document_field = mongoengine.ReferenceField(document)
                document_field = convert_mongoengine_field(document_field, registry)
                document_field_type = document_field.get_type().type
                queried_fields = list()
                filter_args = list()
                if document_field_type._meta.filter_fields:
                    for key, values in document_field_type._meta.filter_fields.items():
                        for each in values:
                            filter_args.append(key + "__" + each)
                for each in get_query_fields(args[0][3][0])[document_field_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                return (
                    document.objects()
                    .no_dereference()
                    .only(*set(list(document_field_type._meta.required_fields) + queried_fields))
                    .filter(pk__in=args[0][1])
                )

            def get_non_querying_object(*args, **kwargs):
                model = get_document(args[0][0])
                return [model(pk=each) for each in args[0][1]]

            def reference_resolver(root, *args, **kwargs):
                to_resolve = getattr(root, field.name or field.db_name)
                if to_resolve:
                    choice_to_resolve = dict()
                    querying_union_types = list(get_query_fields(args[0]).keys())
                    if "__typename" in querying_union_types:
                        querying_union_types.remove("__typename")
                    to_resolve_models = list()
                    for each in querying_union_types:
                        if executor == ExecutorEnum.SYNC:
                            to_resolve_models.append(registry._registry_string_map[each])
                        else:
                            to_resolve_models.append(registry._registry_async_string_map[each])
                    to_resolve_object_ids = list()
                    for each in to_resolve:
                        if isinstance(each, LazyReference):
                            to_resolve_object_ids.append(each.pk)
                            model = each.document_type._class_name
                            if model not in choice_to_resolve:
                                choice_to_resolve[model] = list()
                            choice_to_resolve[model].append(each.pk)
                        else:
                            to_resolve_object_ids.append(each["_ref"].id)
                            if each["_cls"] not in choice_to_resolve:
                                choice_to_resolve[each["_cls"]] = list()
                            choice_to_resolve[each["_cls"]].append(each["_ref"].id)
                    pool = ThreadPoolExecutor(5)
                    futures = list()
                    for model, object_id_list in choice_to_resolve.items():
                        if model in to_resolve_models:
                            futures.append(
                                pool.submit(
                                    get_reference_objects,
                                    (model, object_id_list, registry, args),
                                )
                            )
                        else:
                            futures.append(
                                pool.submit(
                                    get_non_querying_object,
                                    (model, object_id_list, registry, args),
                                )
                            )
                    result = list()
                    for x in as_completed(futures):
                        result += x.result()
                    result_object_ids = list()
                    for each in result:
                        result_object_ids.append(each.id)
                    ordered_result = list()
                    for each in to_resolve_object_ids:
                        ordered_result.append(result[result_object_ids.index(each)])
                    return ordered_result
                return None

            async def get_reference_objects_async(*args, **kwargs):
                document = get_document(args[0])
                document_field = mongoengine.ReferenceField(document)
                document_field = convert_mongoengine_field(
                    document_field, registry, executor=ExecutorEnum.ASYNC
                )
                document_field_type = document_field.get_type().type
                queried_fields = list()
                filter_args = list()
                if document_field_type._meta.filter_fields:
                    for key, values in document_field_type._meta.filter_fields.items():
                        for each in values:
                            filter_args.append(key + "__" + each)
                for each in get_query_fields(args[3][0])[document_field_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                return await sync_to_async(list)(
                    document.objects()
                    .no_dereference()
                    .only(*set(list(document_field_type._meta.required_fields) + queried_fields))
                    .filter(pk__in=args[1])
                )

            async def get_non_querying_object_async(*args, **kwargs):
                model = get_document(args[0])
                return [model(pk=each) for each in args[1]]

            async def reference_resolver_async(root, *args, **kwargs):
                to_resolve = getattr(root, field.name or field.db_name)
                if to_resolve:
                    choice_to_resolve = dict()
                    querying_union_types = list(get_query_fields(args[0]).keys())
                    if "__typename" in querying_union_types:
                        querying_union_types.remove("__typename")
                    to_resolve_models = list()
                    for each in querying_union_types:
                        if executor == ExecutorEnum.SYNC:
                            to_resolve_models.append(registry._registry_string_map[each])
                        else:
                            to_resolve_models.append(registry._registry_async_string_map[each])
                    to_resolve_object_ids = list()
                    for each in to_resolve:
                        if isinstance(each, LazyReference):
                            to_resolve_object_ids.append(each.pk)
                            model = each.document_type._class_name
                            if model not in choice_to_resolve:
                                choice_to_resolve[model] = list()
                            choice_to_resolve[model].append(each.pk)
                        else:
                            to_resolve_object_ids.append(each["_ref"].id)
                            if each["_cls"] not in choice_to_resolve:
                                choice_to_resolve[each["_cls"]] = list()
                            choice_to_resolve[each["_cls"]].append(each["_ref"].id)
                    loop = asyncio.get_event_loop()
                    tasks = []
                    for model, object_id_list in choice_to_resolve.items():
                        if model in to_resolve_models:
                            task = loop.create_task(
                                get_reference_objects_async(model, object_id_list, registry, args)
                            )
                        else:
                            task = loop.create_task(
                                get_non_querying_object_async(model, object_id_list, registry, args)
                            )
                        tasks.append(task)
                    result = await asyncio.gather(*tasks)
                    result_object = {}
                    for items in result:
                        for item in items:
                            result_object[item.id] = item
                    ordered_result = list()
                    for each in to_resolve_object_ids:
                        ordered_result.append(result_object[each])
                    return ordered_result
                return None

            return graphene.List(
                base_type._type,
                description=get_field_description(field, registry),
                required=field.required,
                resolver=reference_resolver
                if executor == ExecutorEnum.SYNC
                else reference_resolver_async,
            )
        return graphene.List(
            base_type._type,
            description=get_field_description(field, registry),
            required=field.required,
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
        required=field.required,
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

    def reference_resolver(root, *args, **kwargs):
        de_referenced = getattr(root, field.name or field.db_name)
        if de_referenced:
            document = get_document(de_referenced["_cls"])
            document_field = mongoengine.ReferenceField(document)
            document_field = convert_mongoengine_field(document_field, registry, executor=executor)
            _type = document_field.get_type().type
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            querying_types = list(get_query_fields(args[0]).keys())
            if _type.__name__ in querying_types:
                queried_fields = list()
                for each in get_query_fields(args[0])[_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                return (
                    document.objects()
                    .no_dereference()
                    .only(*list(set(list(_type._meta.required_fields) + queried_fields)))
                    .get(pk=de_referenced["_ref"].id)
                )
            return document()
        return None

    def lazy_reference_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            if document._cached_doc:
                return document._cached_doc
            queried_fields = list()
            document_field_type = registry.get_type_for_model(
                document.document_type, executor=executor
            )
            querying_types = list(get_query_fields(args[0]).keys())
            filter_args = list()
            if document_field_type._meta.filter_fields:
                for key, values in document_field_type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            if document_field_type._meta.name in querying_types:
                for each in get_query_fields(args[0])[document_field_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document.document_type._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                _type = registry.get_type_for_model(document.document_type, executor=executor)
                return (
                    document.document_type.objects()
                    .no_dereference()
                    .only(*(set((list(_type._meta.required_fields) + queried_fields))))
                    .get(pk=document.pk)
                )
            return document.document_type()
        return None

    async def reference_resolver_async(root, *args, **kwargs):
        de_referenced = getattr(root, field.name or field.db_name)
        if de_referenced:
            document = get_document(de_referenced["_cls"])
            document_field = mongoengine.ReferenceField(document)
            document_field = convert_mongoengine_field(
                document_field, registry, executor=ExecutorEnum.ASYNC
            )
            _type = document_field.get_type().type
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            querying_types = list(get_query_fields(args[0]).keys())
            if _type.__name__ in querying_types:
                queried_fields = list()
                for each in get_query_fields(args[0])[_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                return await sync_to_async(
                    document.objects()
                    .no_dereference()
                    .only(*list(set(list(_type._meta.required_fields) + queried_fields)))
                    .get
                )(pk=de_referenced["_ref"].id)
            return await sync_to_async(document)()
        return None

    async def lazy_reference_resolver_async(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            if document._cached_doc:
                return document._cached_doc
            queried_fields = list()
            document_field_type = registry.get_type_for_model(
                document.document_type, executor=executor
            )
            querying_types = list(get_query_fields(args[0]).keys())
            filter_args = list()
            if document_field_type._meta.filter_fields:
                for key, values in document_field_type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            if document_field_type._meta.name in querying_types:
                for each in get_query_fields(args[0])[document_field_type._meta.name].keys():
                    item = to_snake_case(each)
                    if item in document.document_type._fields_ordered + tuple(filter_args):
                        queried_fields.append(item)
                _type = registry.get_type_for_model(document.document_type, executor=executor)
                return await sync_to_async(
                    document.document_type.objects()
                    .no_dereference()
                    .only(*(set((list(_type._meta.required_fields) + queried_fields))))
                    .get
                )(pk=document.pk)
            return await sync_to_async(document.document_type)()
        return None

    if isinstance(field, mongoengine.GenericLazyReferenceField):
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _union,
            resolver=field_resolver
            if field_resolver
            else (
                lazy_reference_resolver
                if executor == ExecutorEnum.SYNC
                else lazy_reference_resolver_async
            ),
            description=get_field_description(field, registry),
            required=required,
        )

    elif isinstance(field, mongoengine.GenericReferenceField):
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _union,
            resolver=field_resolver
            if field_resolver
            else (
                reference_resolver if executor == ExecutorEnum.SYNC else reference_resolver_async
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

    def reference_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return (
                field.document_type.objects()
                .no_dereference()
                .only(*(set(list(_type._meta.required_fields) + queried_fields)))
                .get(pk=document.id)
            )
        return None

    def cached_reference_resolver(root, *args, **kwargs):
        if field:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return (
                field.document_type.objects()
                .no_dereference()
                .only(*(set(list(_type._meta.required_fields) + queried_fields)))
                .get(pk=getattr(root, field.name or field.db_name))
            )
        return None

    async def reference_resolver_async(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return await sync_to_async(
                field.document_type.objects()
                .no_dereference()
                .only(*(set(list(_type._meta.required_fields) + queried_fields)))
                .get
            )(pk=document.id)
        return None

    async def cached_reference_resolver_async(root, *args, **kwargs):
        if field:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return await sync_to_async(
                field.document_type.objects()
                .no_dereference()
                .only(*(set(list(_type._meta.required_fields) + queried_fields)))
                .get
            )(pk=getattr(root, field.name or field.db_name))
        return None

    def dynamic_type():
        _type = registry.get_type_for_model(model, executor=executor)
        if not _type:
            return None
        if isinstance(field, mongoengine.EmbeddedDocumentField):
            return graphene.Field(
                _type,
                description=get_field_description(field, registry),
                required=field.required,
            )
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        if isinstance(field, mongoengine.ReferenceField):
            return graphene.Field(
                _type,
                resolver=field_resolver
                if field_resolver
                else (
                    reference_resolver
                    if executor == ExecutorEnum.SYNC
                    else reference_resolver_async
                ),
                description=get_field_description(field, registry),
                required=required,
            )
        else:
            return graphene.Field(
                _type,
                resolver=field_resolver
                if field_resolver
                else (
                    cached_reference_resolver
                    if executor == ExecutorEnum.SYNC
                    else cached_reference_resolver_async
                ),
                description=get_field_description(field, registry),
                required=required,
            )

    return graphene.Dynamic(dynamic_type)


@convert_mongoengine_field.register(mongoengine.LazyReferenceField)
def convert_lazy_field_to_dynamic(field, registry=None, executor: ExecutorEnum = ExecutorEnum.SYNC):
    model = field.document_type

    def lazy_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            if document._cached_doc:
                return document._cached_doc
            queried_fields = list()
            _type = registry.get_type_for_model(document.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in document.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return (
                document.document_type.objects()
                .no_dereference()
                .only(*(set((list(_type._meta.required_fields) + queried_fields))))
                .get(pk=document.pk)
            )
        return None

    async def lazy_resolver_async(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            if document._cached_doc:
                return document._cached_doc
            queried_fields = list()
            _type = registry.get_type_for_model(document.document_type, executor=executor)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in document.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return await sync_to_async(
                document.document_type.objects()
                .no_dereference()
                .only(*(set((list(_type._meta.required_fields) + queried_fields))))
                .get
            )(pk=document.pk)
        return None

    def dynamic_type():
        _type = registry.get_type_for_model(model, executor=executor)
        if not _type:
            return None
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(
                registry.get_type_for_model(field.owner_document, executor=executor),
                "resolve_" + field.db_field,
                None,
            )
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _type,
            resolver=field_resolver
            if field_resolver
            else (lazy_resolver if executor == ExecutorEnum.SYNC else lazy_resolver_async),
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
            required=field.required,
        )
