from __future__ import absolute_import

from collections import OrderedDict
from functools import partial, reduce

import graphene
import mongoengine
from bson import DBRef
from graphene import Context
from graphene.types.utils import get_type
from graphene.utils.str_converters import to_snake_case
from graphql import ResolveInfo
from mongoengine.base import get_document
from promise import Promise
from graphql_relay import from_global_id
from graphene.relay import ConnectionField
from graphene.types.argument import to_arguments
from graphene.types.dynamic import Dynamic
from graphene.types.structures import Structure
from graphql_relay.connection.arrayconnection import cursor_to_offset
from mongoengine import QuerySet

from .advanced_types import (
    FileFieldType,
    PointFieldType,
    MultiPolygonFieldType,
    PolygonFieldType,
)
from .converter import convert_mongoengine_field, MongoEngineConversionError
from .registry import get_global_registry
from .utils import get_model_reference_fields, get_query_fields, find_skip_and_limit, \
    connection_from_iterables


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
        return to_arguments(
            self._base_args or OrderedDict(),
            dict(dict(self.field_args, **self.reference_args), **self.filter_args),
        )

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

            if not hasattr(self.model, k):
                return False
            if isinstance(getattr(self.model, k), property):
                return False
            try:
                converted = convert_mongoengine_field(
                    getattr(self.model, k), self.registry
                )
            except MongoEngineConversionError:
                return False
            if isinstance(converted, (ConnectionField, Dynamic)):
                return False
            if callable(getattr(converted, "type", None)) and isinstance(
                    converted.type(),
                    (
                            FileFieldType,
                            MultiPolygonFieldType,
                            graphene.Union,
                            PolygonFieldType,
                    ),
            ):
                return False
            if getattr(converted, "type", None) and getattr(converted.type, "_of_type", None) and issubclass(
                    (get_type(converted.type.of_type)), graphene.Union):
                return False
            if isinstance(converted, (graphene.List)) and issubclass(
                    getattr(converted, "_of_type", None), graphene.Union
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
                    if each == 'max_distance' and str(self._type._meta.fields[field].type) == 'PointFieldType':
                        filter_type = graphene.Int
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
                    filter_args[field + "__" + each] = graphene.Argument(
                        type=filter_type
                    )

        return filter_args

    @property
    def reference_args(self):
        def get_reference_field(r, kv):
            field = kv[1]
            mongo_field = getattr(self.model, kv[0], None)
            if isinstance(
                    mongo_field,
                    (mongoengine.LazyReferenceField, mongoengine.ReferenceField, mongoengine.GenericReferenceField),
            ):
                r.update({kv[0]: graphene.ID()})
                return r
            if callable(getattr(field, "get_type", None)):
                _type = field.get_type()
                if _type:
                    node = _type.type._meta if hasattr(_type.type, "_meta") else _type.type._of_type._meta
                    if "id" in node.fields and not issubclass(
                            node.model, (mongoengine.EmbeddedDocument,)
                    ):
                        r.update({kv[0]: node.fields["id"]._type.of_type()})

            return r

        return reduce(get_reference_field, self.fields.items(), {})

    @property
    def fields(self):
        self._type = get_type(self._type)
        return self._type._meta.fields

    def get_queryset(self, model, info, required_fields=list(), skip=None, limit=None, reversed=False, **args):
        if args:
            reference_fields = get_model_reference_fields(self.model)
            hydrated_references = {}
            for arg_name, arg in args.copy().items():
                if arg_name in reference_fields and not isinstance(arg,
                                                                   mongoengine.base.metaclasses.TopLevelDocumentMetaclass):
                    try:
                        reference_obj = reference_fields[arg_name].document_type(pk=from_global_id(arg)[1])
                    except TypeError:
                        reference_obj = reference_fields[arg_name].document_type(pk=arg)
                    hydrated_references[arg_name] = reference_obj
                elif arg_name in self.model._fields_ordered and isinstance(getattr(self.model, arg_name),
                                                                           mongoengine.fields.GenericReferenceField):
                    reference_obj = get_document(self.registry._registry_string_map[from_global_id(arg)[0]])(
                        pk=from_global_id(arg)[1])
                    hydrated_references[arg_name] = reference_obj
                elif '__near' in arg_name and isinstance(getattr(self.model, arg_name.split('__')[0]),
                                                         mongoengine.fields.PointField):
                    location = args.pop(arg_name, None)
                    hydrated_references[arg_name] = location["coordinates"]
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
            if reversed:
                if self.order_by:
                    order_by = self.order_by + ",-pk"
                else:
                    order_by = "-pk"
                return model.objects(**args).no_dereference().only(*required_fields).order_by(order_by).skip(
                    skip if skip else 0).limit(limit)
            else:
                return model.objects(**args).no_dereference().only(*required_fields).order_by(self.order_by).skip(
                    skip if skip else 0).limit(limit)
        elif skip is not None:
            if reversed:
                order_by = ""
                if self.order_by:
                    order_by = self.order_by + ",-pk"
                else:
                    order_by = "-pk"
                return model.objects(**args).no_dereference().only(*required_fields).order_by(order_by).skip(
                    skip)
            else:
                return model.objects(**args).no_dereference().only(*required_fields).order_by(self.order_by).skip(
                    skip)
        return model.objects(**args).no_dereference().only(*required_fields).order_by(self.order_by)

    def default_resolver(self, _root, info, required_fields=list(), **args):
        args = args or {}
        if _root is not None:
            field_name = to_snake_case(info.field_name)
            if field_name in _root._fields_ordered and not (isinstance(_root._fields[field_name].field,
                                                                       mongoengine.EmbeddedDocumentField) or
                                                            isinstance(_root._fields[field_name].field,
                                                                       mongoengine.GenericEmbeddedDocumentField)):
                if getattr(_root, field_name, []) is not None:
                    args["pk__in"] = [r.id for r in getattr(_root, field_name, [])]

        _id = args.pop('id', None)

        if _id is not None:
            args['pk'] = from_global_id(_id)[-1]
        iterables = []
        list_length = 0
        skip = 0
        count = 0
        limit = None
        reverse = False
        first = args.pop("first", None)
        after = cursor_to_offset(args.pop("after", None))
        last = args.pop("last", None)
        before = cursor_to_offset(args.pop("before", None))
        if callable(getattr(self.model, "objects", None)):
            if "pk__in" in args and args["pk__in"]:
                count = len(args["pk__in"])
                skip, limit, reverse = find_skip_and_limit(first=first, last=last, after=after, before=before,
                                                           count=count)
                if limit:
                    if reverse:
                        args["pk__in"] = args["pk__in"][::-1][skip:skip + limit]
                    else:
                        args["pk__in"] = args["pk__in"][skip:skip + limit]
                elif skip:
                    args["pk__in"] = args["pk__in"][skip:]
                iterables = self.get_queryset(self.model, info, required_fields, **args)
                list_length = len(iterables)
                if isinstance(info, ResolveInfo):
                    if not info.context:
                        info.context = Context()
                    info.context.queryset = self.get_queryset(self.model, info, required_fields, **args)
            elif _root is None or args:
                count = self.get_queryset(self.model, info, required_fields, **args).count()
                if count != 0:
                    skip, limit, reverse = find_skip_and_limit(first=first, after=after, last=last, before=before,
                                                               count=count)
                    iterables = self.get_queryset(self.model, info, required_fields, skip, limit, reverse, **args)
                    list_length = len(iterables)
                    if isinstance(info, ResolveInfo):
                        if not info.context:
                            info.context = Context()
                        info.context.queryset = self.get_queryset(self.model, info, required_fields, **args)

        elif _root is not None:
            field_name = to_snake_case(info.field_name)
            items = getattr(_root, field_name, [])
            count = len(items)
            skip, limit, reverse = find_skip_and_limit(first=first, last=last, after=after, before=before,
                                                       count=count)
            if limit:
                if reverse:
                    items = items[::-1][skip:skip + limit]
                else:
                    items = items[skip:skip + limit]
            elif skip:
                items = items[skip:]
            iterables = items
            list_length = len(iterables)
        has_next_page = True if (0 if limit is None else limit) + (0 if skip is None else skip) < count else False
        has_previous_page = True if skip else False
        if reverse:
            iterables = list(iterables)
            iterables.reverse()
            skip = limit
        connection = connection_from_iterables(edges=iterables, start_offset=skip,
                                               has_previous_page=has_previous_page,
                                               has_next_page=has_next_page,
                                               connection_type=self.type,
                                               edge_type=self.type.Edge,
                                               pageinfo_type=graphene.PageInfo)

        connection.iterable = iterables
        connection.list_length = list_length
        return connection

    def chained_resolver(self, resolver, is_partial, root, info, **args):
        required_fields = list()
        for field in self.required_fields:
            if field in self.model._fields_ordered:
                required_fields.append(field)
        for field in get_query_fields(info):
            if to_snake_case(field) in self.model._fields_ordered:
                required_fields.append(to_snake_case(field))
        if not bool(args) or not is_partial:
            if isinstance(self.model, mongoengine.Document) or isinstance(self.model,
                                                                          mongoengine.base.metaclasses.TopLevelDocumentMetaclass):
                args_copy = args.copy()
                for arg_name, arg in args.copy().items():
                    if arg_name not in self.model._fields_ordered + tuple(self.filter_args.keys()):
                        args_copy.pop(arg_name)
                if isinstance(info, ResolveInfo):
                    if not info.context:
                        info.context = Context()
                    info.context.queryset = self.get_queryset(self.model, info, required_fields, **args_copy)
            # XXX: Filter nested args
            resolved = resolver(root, info, **args)
            if resolved is not None:
                if isinstance(resolved, list):
                    if resolved == list():
                        return resolved
                    elif not isinstance(resolved[0], DBRef):
                        return resolved
                elif isinstance(resolved, QuerySet):
                    args.update(resolved._query)
                    args_copy = args.copy()
                    for arg_name, arg in args.copy().items():
                        if arg_name not in self.model._fields_ordered + ('first', 'last', 'before', 'after') + tuple(
                                self.filter_args.keys()):
                            args_copy.pop(arg_name)
                            if '.' in arg_name:
                                operation = list(arg.keys())[0]
                                args_copy[arg_name.replace('.', '__') + operation.replace('$', '__')] = arg[operation]
                    return self.default_resolver(root, info, required_fields, **args_copy)
                else:
                    return resolved
        return self.default_resolver(root, info, required_fields, **args)

    @classmethod
    def connection_resolver(cls, resolver, connection_type, root, info, **args):
        iterable = resolver(root, info, **args)
        if isinstance(connection_type, graphene.NonNull):
            connection_type = connection_type.of_type
        on_resolve = partial(cls.resolve_connection, connection_type, args)
        if Promise.is_thenable(iterable):
            return Promise.resolve(iterable).then(on_resolve)
        return on_resolve(iterable)

    def get_resolver(self, parent_resolver):
        super_resolver = self.resolver or parent_resolver
        resolver = partial(
            self.chained_resolver, super_resolver, isinstance(super_resolver, partial)
        )
        return partial(self.connection_resolver, resolver, self.type)
