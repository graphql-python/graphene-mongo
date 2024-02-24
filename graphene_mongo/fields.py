from __future__ import absolute_import

import logging
from collections import OrderedDict
from functools import partial, reduce
from itertools import filterfalse

import bson
import graphene
import mongoengine
import pymongo
from bson import DBRef, ObjectId
from graphene import Context
from graphene.relay import ConnectionField
from graphene.types.argument import to_arguments
from graphene.types.dynamic import Dynamic
from graphene.types.structures import Structure
from graphene.types.utils import get_type
from graphene.utils.str_converters import to_snake_case
from graphql import GraphQLResolveInfo
from graphql_relay import cursor_to_offset, from_global_id
from mongoengine import QuerySet
from mongoengine.base import get_document
from promise import Promise
from pymongo.errors import OperationFailure

from .advanced_types import (
    FileFieldType,
    MultiPolygonFieldType,
    PointFieldInputType,
    PointFieldType,
    PolygonFieldType,
)
from .converter import MongoEngineConversionError, convert_mongoengine_field
from .registry import get_global_registry
from .utils import (
    ExecutorEnum,
    connection_from_iterables,
    find_skip_and_limit,
    get_model_reference_fields,
    get_query_fields,
    has_page_info,
)

PYMONGO_VERSION = tuple(pymongo.version_tuple[:2])


class MongoengineConnectionField(ConnectionField):
    def __init__(self, type, *args, **kwargs):
        get_queryset = kwargs.pop("get_queryset", None)
        if get_queryset:
            assert callable(
                get_queryset
            ), "Attribute `get_queryset` on {} must be callable.".format(self)
        self._get_queryset = get_queryset
        super(MongoengineConnectionField, self).__init__(type, *args, **kwargs)

    @property
    def executor(self) -> ExecutorEnum:
        return ExecutorEnum.SYNC

    @property
    def type(self):
        from .types import MongoengineObjectType

        _type = super(ConnectionField, self).type
        assert issubclass(
            _type, MongoengineObjectType
        ), "MongoengineConnectionField only accepts MongoengineObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(
            _type.__name__
        )
        return _type._meta.connection

    @property
    def node_type(self):
        return self.type._meta.node

    @property
    def model(self):
        return self.node_type._meta.model

    @property
    def order_by(self):
        return self.node_type._meta.order_by

    @property
    def required_fields(self):
        return tuple(set(self.node_type._meta.required_fields + self.node_type._meta.only_fields))

    @property
    def registry(self):
        return getattr(self.node_type._meta, "registry", get_global_registry())

    @property
    def args(self):
        _field_args = self.field_args
        _advance_args = self.advance_args
        _filter_args = self.filter_args
        _extended_args = self.extended_args
        if self._type._meta.non_filter_fields:
            for _field in self._type._meta.non_filter_fields:
                if _field in _field_args:
                    _field_args.pop(_field)
                if _field in _advance_args:
                    _advance_args.pop(_field)
                if _field in _filter_args:
                    _filter_args.pop(_field)
                if _field in _extended_args:
                    _filter_args.pop(_field)
        extra_args = dict(
            dict(dict(_field_args, **_advance_args), **_filter_args), **_extended_args
        )

        for key in list(self._base_args.keys()):
            extra_args.pop(key, None)
        return to_arguments(self._base_args or OrderedDict(), extra_args)

    @args.setter
    def args(self, args):
        self._base_args = args

    def _field_args(self, items):
        def is_filterable(k):
            """
            Remove complex columns from input args at this moment.

            Args:
                k (str): field name.
            Returns:
                bool
            """
            if hasattr(self.fields[k].type, "_sdl"):
                return False
            if not hasattr(self.model, k):
                return False
            else:
                # else section is a patch for federated field error
                field_ = self.fields[k]
                type_ = field_.type
                while hasattr(type_, "of_type"):
                    type_ = type_.of_type
                if hasattr(type_, "_sdl") and "@key" in type_._sdl:
                    return False
            if isinstance(getattr(self.model, k), property):
                return False
            try:
                converted = convert_mongoengine_field(
                    getattr(self.model, k), self.registry, self.executor
                )
            except MongoEngineConversionError:
                return False
            if isinstance(converted, (ConnectionField, Dynamic)):
                return False
            if callable(getattr(converted, "type", None)) and isinstance(
                converted.type(),
                (
                    FileFieldType,
                    PointFieldType,
                    MultiPolygonFieldType,
                    graphene.Union,
                    PolygonFieldType,
                ),
            ):
                return False
            if (
                getattr(converted, "type", None)
                and getattr(converted.type, "_of_type", None)
                and issubclass((get_type(converted.type.of_type)), graphene.Union)
            ):
                return False
            if isinstance(converted, (graphene.List)) and issubclass(
                getattr(converted, "_of_type", None), graphene.Union
            ):
                return False
            # below if condition: workaround for DB filterable field redefined as custom graphene type
            if (
                hasattr(field_, "type")
                and hasattr(converted, "type")
                and converted.type != field_.type
            ):
                return False
            return True

        def get_filter_type(_type):
            """
            Returns the scalar type.
            """
            if isinstance(_type, Structure):
                return get_filter_type(_type.of_type)
            return _type()

        return {k: get_filter_type(v.type) for k, v in items if is_filterable(k)}

    @property
    def field_args(self):
        return self._field_args(self.fields.items())

    @property
    def filter_args(self):
        filter_args = dict()
        if self._type._meta.filter_fields:
            for field, filter_collection in self._type._meta.filter_fields.items():
                for each in filter_collection:
                    if str(self._type._meta.fields[field].type) in (
                        "PointFieldType",
                        "PointFieldType!",
                    ):
                        if each == "max_distance":
                            filter_type = graphene.Int
                        else:
                            filter_type = PointFieldInputType
                    else:
                        filter_type = getattr(
                            graphene,
                            str(self._type._meta.fields[field].type).replace("!", ""),
                        )
                    # handle special cases
                    advanced_filter_types = {
                        "in": graphene.List(filter_type),
                        "nin": graphene.List(filter_type),
                        "all": graphene.List(filter_type),
                    }
                    filter_type = advanced_filter_types.get(each, filter_type)
                    filter_args[field + "__" + each] = graphene.Argument(type_=filter_type)
        return filter_args

    @property
    def advance_args(self):
        def get_advance_field(r, kv):
            field = kv[1]
            mongo_field = getattr(self.model, kv[0], None)
            if isinstance(mongo_field, mongoengine.PointField):
                r.update({kv[0]: graphene.Argument(PointFieldInputType)})
                return r
            if isinstance(
                mongo_field,
                (
                    mongoengine.LazyReferenceField,
                    mongoengine.ReferenceField,
                    mongoengine.GenericReferenceField,
                ),
            ):
                r.update({kv[0]: graphene.ID()})
                return r
            if isinstance(mongo_field, mongoengine.GenericReferenceField):
                r.update({kv[0]: graphene.ID()})
                return r
            if callable(getattr(field, "get_type", None)):
                _type = field.get_type()
                if _type:
                    node = (
                        _type.type._meta
                        if hasattr(_type.type, "_meta")
                        else _type.type._of_type._meta
                    )
                    if "id" in node.fields and not issubclass(
                        node.model, (mongoengine.EmbeddedDocument,)
                    ):
                        r.update({kv[0]: node.fields["id"]._type.of_type()})

            return r

        return reduce(get_advance_field, self.fields.items(), {})

    @property
    def extended_args(self):
        args = OrderedDict()
        for k, each in self.fields.items():
            if hasattr(each.type, "_sdl"):
                args.update({k: graphene.ID()})
        return args

    @property
    def fields(self):
        self._type = get_type(self._type)
        return self._type._meta.fields

    def get_queryset(
        self, model, info, required_fields=None, skip=None, limit=None, **args
    ) -> QuerySet:
        if required_fields is None:
            required_fields = list()

        if args:
            reference_fields = get_model_reference_fields(self.model)
            hydrated_references = {}
            for arg_name, arg in args.copy().items():
                if arg_name in reference_fields and not isinstance(
                    arg, mongoengine.base.metaclasses.TopLevelDocumentMetaclass
                ):
                    try:
                        reference_obj = reference_fields[arg_name].document_type(
                            pk=from_global_id(arg)[1]
                        )
                    except TypeError:
                        reference_obj = reference_fields[arg_name].document_type(pk=arg)
                    hydrated_references[arg_name] = reference_obj
                elif arg_name in self.model._fields_ordered and isinstance(
                    getattr(self.model, arg_name),
                    mongoengine.fields.GenericReferenceField,
                ):
                    try:
                        reference_obj = get_document(
                            self.registry._registry_string_map[from_global_id(arg)[0]]
                        )(pk=from_global_id(arg)[1])
                    except TypeError:
                        reference_obj = get_document(arg["_cls"])(pk=arg["_ref"].id)
                    hydrated_references[arg_name] = reference_obj
                elif "__near" in arg_name and isinstance(
                    getattr(self.model, arg_name.split("__")[0]),
                    mongoengine.fields.PointField,
                ):
                    location = args.pop(arg_name, None)
                    hydrated_references[arg_name] = location["coordinates"]
                    if (arg_name.split("__")[0] + "__max_distance") not in args:
                        hydrated_references[arg_name.split("__")[0] + "__max_distance"] = 10000
                elif arg_name == "id":
                    hydrated_references["id"] = from_global_id(args.pop("id", None))[1]
            args.update(hydrated_references)

        if self._get_queryset:
            queryset_or_filters = self._get_queryset(model, info, **args)
            if isinstance(queryset_or_filters, mongoengine.QuerySet):
                return queryset_or_filters
            else:
                args.update(queryset_or_filters)
        if limit is not None:
            return (
                model.objects(**args)
                .no_dereference()
                .only(*required_fields)
                .order_by(self.order_by)
                .skip(skip if skip else 0)
                .limit(limit)
            )
        elif skip is not None:
            return (
                model.objects(**args)
                .no_dereference()
                .only(*required_fields)
                .order_by(self.order_by)
                .skip(skip)
            )
        return model.objects(**args).no_dereference().only(*required_fields).order_by(self.order_by)

    def default_resolver(self, _root, info, required_fields=None, resolved=None, **args):
        if required_fields is None:
            required_fields = list()
        args = args or {}
        for key, value in dict(args).items():
            if value is None:
                del args[key]
        if _root is not None and not resolved:
            field_name = to_snake_case(info.field_name)
            if not hasattr(_root, "_fields_ordered"):
                if isinstance(getattr(_root, field_name, []), list):
                    args["pk__in"] = [r.id for r in getattr(_root, field_name, [])]
            elif field_name in _root._fields_ordered and not (
                isinstance(_root._fields[field_name].field, mongoengine.EmbeddedDocumentField)
                or isinstance(
                    _root._fields[field_name].field,
                    mongoengine.GenericEmbeddedDocumentField,
                )
            ):
                if getattr(_root, field_name, []) is not None:
                    args["pk__in"] = [r.id for r in getattr(_root, field_name, [])]

        _id = args.pop("id", None)

        if _id is not None:
            args["pk"] = from_global_id(_id)[-1]
        iterables = []
        list_length = 0
        skip = 0
        count = 0
        limit = None
        first = args.pop("first", None)
        after = args.pop("after", None)
        if after:
            after = cursor_to_offset(after)
        last = args.pop("last", None)
        before = args.pop("before", None)
        if before:
            before = cursor_to_offset(before)
        requires_page_info = has_page_info(info)
        has_next_page = False

        if resolved is not None:
            items = resolved

            if isinstance(items, QuerySet):
                try:
                    if last is not None:
                        count = items.count(with_limit_and_skip=False)
                    else:
                        count = None
                except OperationFailure:
                    count = len(items)
            else:
                count = len(items)

            skip, limit = find_skip_and_limit(
                first=first, last=last, after=after, before=before, count=count
            )

            if isinstance(items, QuerySet):
                if limit:
                    _base_query: QuerySet = items.skip(skip)
                    items = _base_query.limit(limit)
                    has_next_page = len(_base_query.skip(skip + limit).only("id").limit(1)) != 0
                elif skip:
                    items = items.skip(skip)
            else:
                if limit:
                    _base_query = items
                    items = items[skip : skip + limit]
                    has_next_page = (
                        (skip + limit) < len(_base_query) if requires_page_info else False
                    )
                elif skip:
                    items = items[skip:]
            iterables = list(items)
            list_length = len(iterables)

        elif callable(getattr(self.model, "objects", None)):
            if (
                _root is None
                or args
                or isinstance(getattr(_root, field_name, []), MongoengineConnectionField)
            ):
                args_copy = args.copy()
                for key in args.copy():
                    if key not in self.model._fields_ordered:
                        args_copy.pop(key)
                    elif (
                        isinstance(getattr(self.model, key), mongoengine.fields.ReferenceField)
                        or isinstance(
                            getattr(self.model, key),
                            mongoengine.fields.GenericReferenceField,
                        )
                        or isinstance(
                            getattr(self.model, key),
                            mongoengine.fields.LazyReferenceField,
                        )
                        or isinstance(
                            getattr(self.model, key),
                            mongoengine.fields.CachedReferenceField,
                        )
                    ):
                        if not isinstance(args_copy[key], ObjectId):
                            _from_global_id = from_global_id(args_copy[key])[1]
                            if bson.objectid.ObjectId.is_valid(_from_global_id):
                                args_copy[key] = ObjectId(_from_global_id)
                            else:
                                args_copy[key] = _from_global_id
                    elif isinstance(getattr(self.model, key), mongoengine.fields.EnumField):
                        if getattr(args_copy[key], "value", None):
                            args_copy[key] = args_copy[key].value

                if PYMONGO_VERSION >= (3, 7):
                    if hasattr(self.model, "_meta") and "db_alias" in self.model._meta:
                        count = (
                            mongoengine.get_db(self.model._meta["db_alias"])[
                                self.model._get_collection_name()
                            ]
                        ).count_documents(args_copy)
                    else:
                        count = (
                            mongoengine.get_db()[self.model._get_collection_name()]
                        ).count_documents(args_copy)
                else:
                    count = self.model.objects(args_copy).count()
                if count != 0:
                    skip, limit = find_skip_and_limit(
                        first=first, after=after, last=last, before=before, count=count
                    )
                    iterables = self.get_queryset(
                        self.model, info, required_fields, skip, limit, **args
                    )
                    list_length = len(iterables)
                    if isinstance(info, GraphQLResolveInfo):
                        if not info.context:
                            info = info._replace(context=Context())
                        info.context.queryset = self.get_queryset(
                            self.model, info, required_fields, **args
                        )

            elif "pk__in" in args and args["pk__in"]:
                count = len(args["pk__in"])
                skip, limit = find_skip_and_limit(
                    first=first, last=last, after=after, before=before, count=count
                )
                if limit:
                    args["pk__in"] = args["pk__in"][skip : skip + limit]
                elif skip:
                    args["pk__in"] = args["pk__in"][skip:]
                iterables = self.get_queryset(self.model, info, required_fields, **args)
                list_length = len(iterables)
                if isinstance(info, GraphQLResolveInfo):
                    if not info.context:
                        info = info._replace(context=Context())
                    info.context.queryset = self.get_queryset(
                        self.model, info, required_fields, **args
                    )

        elif _root is not None:
            field_name = to_snake_case(info.field_name)
            items = getattr(_root, field_name, [])
            count = len(items)
            skip, limit = find_skip_and_limit(
                first=first, last=last, after=after, before=before, count=count
            )
            if limit:
                _base_query = items
                items = items[skip : skip + limit]
                has_next_page = (skip + limit) < len(_base_query) if requires_page_info else False
            elif skip:
                items = items[skip:]
            iterables = items
            list_length = len(iterables)

        if count:
            has_next_page = (
                True
                if (0 if limit is None else limit) + (0 if skip is None else skip) < count
                else False
            )
        has_previous_page = True if skip else False

        connection = connection_from_iterables(
            edges=iterables,
            start_offset=skip,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page,
            connection_type=self.type,
            edge_type=self.type.Edge,
            pageinfo_type=graphene.PageInfo,
        )
        connection.iterable = iterables
        connection.list_length = list_length
        return connection

    def chained_resolver(self, resolver, is_partial, root, info, **args):
        for key, value in dict(args).items():
            if value is None:
                del args[key]

        required_fields = list()

        for field in self.required_fields:
            if field in self.model._fields_ordered:
                required_fields.append(field)

        for field in get_query_fields(info):
            if to_snake_case(field) in self.model._fields_ordered:
                required_fields.append(to_snake_case(field))

        args_copy = args.copy()

        if not bool(args) or not is_partial:
            if isinstance(self.model, mongoengine.Document) or isinstance(
                self.model, mongoengine.base.metaclasses.TopLevelDocumentMetaclass
            ):
                connection_fields = [
                    field
                    for field in self.fields
                    if isinstance(self.fields[field], MongoengineConnectionField)
                ]

                def filter_connection(x):
                    return any(
                        [
                            connection_fields.__contains__(x),
                            self._type._meta.non_filter_fields.__contains__(x),
                        ]
                    )

                filterable_args = tuple(
                    filterfalse(filter_connection, list(self.model._fields_ordered))
                )
                for arg_name, arg in args.copy().items():
                    if arg_name not in filterable_args + tuple(self.filter_args.keys()):
                        args_copy.pop(arg_name)
                if isinstance(info, GraphQLResolveInfo):
                    if not info.context:
                        info = info._replace(context=Context())
                    info.context.queryset = self.get_queryset(
                        self.model, info, required_fields, **args_copy
                    )

            # XXX: Filter nested args
            resolved = resolver(root, info, **args)

            if resolved is not None:
                if isinstance(resolved, list):
                    if resolved == list():
                        return resolved
                    elif not isinstance(resolved[0], DBRef):
                        return resolved
                    else:
                        return self.default_resolver(root, info, required_fields, **args_copy)
                elif isinstance(resolved, QuerySet):
                    args.update(resolved._query)
                    args_copy = args.copy()
                    for arg_name, arg in args.copy().items():
                        if "." in arg_name or arg_name not in self.model._fields_ordered + (
                            "first",
                            "last",
                            "before",
                            "after",
                        ) + tuple(self.filter_args.keys()):
                            args_copy.pop(arg_name)
                            if arg_name == "_id" and isinstance(arg, dict):
                                operation = list(arg.keys())[0]
                                args_copy["pk" + operation.replace("$", "__")] = arg[operation]
                            if not isinstance(arg, ObjectId) and "." in arg_name:
                                if isinstance(arg, dict):
                                    operation = list(arg.keys())[0]
                                    args_copy[
                                        arg_name.replace(".", "__") + operation.replace("$", "__")
                                    ] = arg[operation]
                                else:
                                    args_copy[arg_name.replace(".", "__")] = arg
                            elif "." in arg_name and isinstance(arg, ObjectId):
                                args_copy[arg_name.replace(".", "__")] = arg
                        else:
                            operations = ["$lte", "$gte", "$ne", "$in"]
                            if isinstance(arg, dict) and any(op in arg for op in operations):
                                operation = list(arg.keys())[0]
                                args_copy[arg_name + operation.replace("$", "__")] = arg[operation]
                                del args_copy[arg_name]
                    return self.default_resolver(
                        root, info, required_fields, resolved=resolved, **args_copy
                    )
                elif isinstance(resolved, Promise):
                    return resolved.value
                else:
                    return resolved

        return self.default_resolver(root, info, required_fields, **args)

    @classmethod
    def connection_resolver(cls, resolver, connection_type, root, info, **args):
        if root:
            for key, value in root.__dict__.items():
                if value:
                    try:
                        setattr(root, key, from_global_id(value)[1])
                    except Exception as error:
                        logging.debug("Exception Occurred: ", exc_info=error)
        iterable = resolver(root, info, **args)

        if isinstance(connection_type, graphene.NonNull):
            connection_type = connection_type.of_type

        on_resolve = partial(cls.resolve_connection, connection_type, args)

        if Promise.is_thenable(iterable):
            return Promise.resolve(iterable).then(on_resolve)

        return on_resolve(iterable)

    def wrap_resolve(self, parent_resolver):
        super_resolver = self.resolver or parent_resolver
        resolver = partial(
            self.chained_resolver, super_resolver, isinstance(super_resolver, partial)
        )
        return partial(self.connection_resolver, resolver, self.type)
