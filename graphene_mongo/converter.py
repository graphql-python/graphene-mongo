import sys

import graphene
import mongoengine
import uuid

from graphene.types.json import JSONString
from graphene.utils.str_converters import to_snake_case
from mongoengine.base import get_document, LazyReference
from . import advanced_types
from .utils import import_single_dispatch, get_field_description, get_query_fields
from concurrent.futures import ThreadPoolExecutor, as_completed

singledispatch = import_single_dispatch()


class MongoEngineConversionError(Exception):
    pass


@singledispatch
def convert_mongoengine_field(field, registry=None):
    raise MongoEngineConversionError(
        "Don't know how to convert the MongoEngine field %s (%s)"
        % (field, field.__class__)
    )


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None):
    return graphene.String(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None):
    return graphene.ID(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.IntField)
@convert_mongoengine_field.register(mongoengine.LongField)
@convert_mongoengine_field.register(mongoengine.SequenceField)
def convert_field_to_int(field, registry=None):
    return graphene.Int(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return graphene.Boolean(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DecimalField)
@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None):
    return graphene.Float(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_field_to_datetime(field, registry=None):
    return graphene.DateTime(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_field_to_jsonstring(field, registry=None):
    return JSONString(
        description=get_field_description(field, registry), required=field.required
    )


@convert_mongoengine_field.register(mongoengine.PointField)
def convert_point_to_field(field, registry=None):
    return graphene.Field(advanced_types.PointFieldType, description=get_field_description(field, registry),
                          required=field.required)


@convert_mongoengine_field.register(mongoengine.PolygonField)
def convert_polygon_to_field(field, registry=None):
    return graphene.Field(advanced_types.PolygonFieldType, description=get_field_description(field, registry),
                          required=field.required)


@convert_mongoengine_field.register(mongoengine.MultiPolygonField)
def convert_multipolygon_to_field(field, registry=None):
    return graphene.Field(advanced_types.MultiPolygonFieldType, description=get_field_description(field, registry),
                          required=field.required)


@convert_mongoengine_field.register(mongoengine.FileField)
def convert_file_to_field(field, registry=None):
    return graphene.Field(advanced_types.FileFieldType, description=get_field_description(field, registry),
                          required=field.required)


@convert_mongoengine_field.register(mongoengine.ListField)
@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentListField)
@convert_mongoengine_field.register(mongoengine.GeoPointField)
def convert_field_to_list(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
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
                return document.objects().no_dereference().only(
                    *set(list(document_field_type._meta.required_fields) + queried_fields)).filter(pk__in=args[0][1])

            def get_non_querying_object(*args, **kwargs):
                model = get_document(args[0][0])
                return [model(pk=each) for each in args[0][1]]

            def reference_resolver(root, *args, **kwargs):
                to_resolve = getattr(root, field.name or field.db_name)
                if to_resolve:
                    choice_to_resolve = dict()
                    querying_union_types = list(get_query_fields(args[0]).keys())
                    if '__typename' in querying_union_types:
                        querying_union_types.remove('__typename')
                    to_resolve_models = list()
                    for each in querying_union_types:
                        to_resolve_models.append(registry._registry_string_map[each])
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
                            if each['_cls'] not in choice_to_resolve:
                                choice_to_resolve[each['_cls']] = list()
                            choice_to_resolve[each['_cls']].append(each["_ref"].id)
                    pool = ThreadPoolExecutor(5)
                    futures = list()
                    for model, object_id_list in choice_to_resolve.items():
                        if model in to_resolve_models:
                            futures.append(pool.submit(get_reference_objects, (model, object_id_list, registry, args)))
                        else:
                            futures.append(
                                pool.submit(get_non_querying_object, (model, object_id_list, registry, args)))
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

            return graphene.List(
                base_type._type,
                description=get_field_description(field, registry),
                required=field.required,
                resolver=reference_resolver
            )
        return graphene.List(
            base_type._type,
            description=get_field_description(field, registry),
            required=field.required
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
def convert_field_to_union(field, registry=None):
    _types = []
    for choice in field.choices:
        if isinstance(field, mongoengine.GenericReferenceField):
            _field = mongoengine.ReferenceField(get_document(choice))
        elif isinstance(field, mongoengine.GenericEmbeddedDocumentField):
            _field = mongoengine.EmbeddedDocumentField(choice)

        _field = convert_mongoengine_field(_field, registry)
        _type = _field.get_type()
        if _type:
            _types.append(_type.type)
        else:
            # TODO: Register type auto-matically here.
            pass

    if len(_types) == 0:
        return None

    # XXX: Use uuid to avoid duplicate name
    name = "{}_{}_union_{}".format(
        field._owner_document.__name__,
        field.db_field,
        str(uuid.uuid1()).replace("-", ""),
    )
    Meta = type("Meta", (object,), {"types": tuple(_types)})
    _union = type(name, (graphene.Union,), {"Meta": Meta})

    def reference_resolver(root, *args, **kwargs):
        de_referenced = getattr(root, field.name or field.db_name)
        if de_referenced:
            document = get_document(de_referenced["_cls"])
            document_field = mongoengine.ReferenceField(document)
            document_field = convert_mongoengine_field(document_field, registry)
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
                return document.objects().no_dereference().only(*list(
                    set(list(_type._meta.required_fields) + queried_fields))).get(
                    pk=de_referenced["_ref"].id)
            return document()
        return None

    def lazy_reference_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            queried_fields = list()
            document_field_type = registry.get_type_for_model(document.document_type)
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
                _type = registry.get_type_for_model(document.document_type)
                return document.document_type.objects().no_dereference().only(
                    *(set((list(_type._meta.required_fields) + queried_fields)))).get(
                    pk=document.pk)
            return document.document_type()
        return None

    if isinstance(field, mongoengine.GenericLazyReferenceField):
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(registry.get_type_for_model(field.owner_document), "resolve_" + field.db_field,
                                        None)
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(_union, resolver=field_resolver if field_resolver else lazy_reference_resolver,
                              description=get_field_description(field, registry), required=required)

    elif isinstance(field, mongoengine.GenericReferenceField):
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(registry.get_type_for_model(field.owner_document), "resolve_" + field.db_field,
                                        None)
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(_union, resolver=field_resolver if field_resolver else reference_resolver,
                              description=get_field_description(field, registry), required=required)

    return graphene.Field(_union)


@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentField)
@convert_mongoengine_field.register(mongoengine.ReferenceField)
@convert_mongoengine_field.register(mongoengine.CachedReferenceField)
def convert_field_to_dynamic(field, registry=None):
    model = field.document_type

    def reference_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return field.document_type.objects().no_dereference().only(
                *(set(list(_type._meta.required_fields) + queried_fields))).get(
                pk=document.id)
        return None

    def cached_reference_resolver(root, *args, **kwargs):
        if field:
            queried_fields = list()
            _type = registry.get_type_for_model(field.document_type)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in field.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return field.document_type.objects().no_dereference().only(
                *(set(
                    list(_type._meta.required_fields) + queried_fields))).get(
                pk=getattr(root, field.name or field.db_name))
        return None

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        if isinstance(field, mongoengine.EmbeddedDocumentField):
            return graphene.Field(_type,
                                  description=get_field_description(field, registry), required=field.required)
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(registry.get_type_for_model(field.owner_document), "resolve_" + field.db_field,
                                        None)
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        if isinstance(field, mongoengine.ReferenceField):
            return graphene.Field(_type, resolver=field_resolver if field_resolver else reference_resolver,
                                  description=get_field_description(field, registry), required=required)
        else:
            return graphene.Field(_type, resolver=field_resolver if field_resolver else cached_reference_resolver,
                                  description=get_field_description(field, registry), required=required)

    return graphene.Dynamic(dynamic_type)


@convert_mongoengine_field.register(mongoengine.LazyReferenceField)
def convert_lazy_field_to_dynamic(field, registry=None):
    model = field.document_type

    def lazy_resolver(root, *args, **kwargs):
        document = getattr(root, field.name or field.db_name)
        if document:
            queried_fields = list()
            _type = registry.get_type_for_model(document.document_type)
            filter_args = list()
            if _type._meta.filter_fields:
                for key, values in _type._meta.filter_fields.items():
                    for each in values:
                        filter_args.append(key + "__" + each)
            for each in get_query_fields(args[0]).keys():
                item = to_snake_case(each)
                if item in document.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            return document.document_type.objects().no_dereference().only(
                *(set((list(_type._meta.required_fields) + queried_fields)))).get(
                pk=document.pk)
        return None

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        field_resolver = None
        required = False
        if field.db_field is not None:
            required = field.required
            resolver_function = getattr(registry.get_type_for_model(field.owner_document), "resolve_" + field.db_field,
                                        None)
            if resolver_function and callable(resolver_function):
                field_resolver = resolver_function
        return graphene.Field(
            _type,
            resolver=field_resolver if field_resolver else lazy_resolver,
            description=get_field_description(field, registry), required=required,
        )

    return graphene.Dynamic(dynamic_type)


if sys.version_info >= (3, 6):
    @convert_mongoengine_field.register(mongoengine.EnumField)
    def convert_field_to_enum(field, registry=None):
        if not registry.check_enum_already_exist(field._enum_cls):
            registry.register_enum(field._enum_cls)
        _type = registry.get_type_for_enum(field._enum_cls)
        return graphene.Field(_type,
                              description=get_field_description(field, registry), required=field.required)
