from __future__ import absolute_import

from collections import OrderedDict
from functools import partial, reduce

import graphene
import mongoengine
from promise import Promise
from graphql_relay import from_global_id
from graphene.relay import ConnectionField
from graphene.types.argument import to_arguments
from graphene.types.dynamic import Dynamic
from graphene.types.structures import Structure
from graphql_relay.connection.arrayconnection import connection_from_list_slice

from .advanced_types import (
    FileFieldType,
    PointFieldType,
    MultiPolygonFieldType,
    PolygonFieldType,
)
from .converter import convert_mongoengine_field, MongoEngineConversionError
from .registry import get_global_registry
from .utils import get_model_reference_fields, get_node_from_global_id


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
                    PointFieldType,
                    MultiPolygonFieldType,
                    graphene.Union,
                    PolygonFieldType,
                ),
            ):
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
                (mongoengine.LazyReferenceField, mongoengine.ReferenceField),
            ):
                field = convert_mongoengine_field(mongo_field, self.registry)
            if callable(getattr(field, "get_type", None)):
                _type = field.get_type()
                if _type:
                    node = _type._type._meta
                    if "id" in node.fields and not issubclass(
                        node.model, (mongoengine.EmbeddedDocument,)
                    ):
                        r.update({kv[0]: node.fields["id"]._type.of_type()})
            return r

        return reduce(get_reference_field, self.fields.items(), {})

    @property
    def fields(self):
        return self._type._meta.fields

    def get_queryset(self, model, info, **args):
        if args:
            reference_fields = get_model_reference_fields(self.model)
            hydrated_references = {}
            for arg_name, arg in args.copy().items():
                if arg_name in reference_fields:
                    reference_obj = get_node_from_global_id(
                        reference_fields[arg_name], info, args.pop(arg_name)
                    )
                    hydrated_references[arg_name] = reference_obj
            args.update(hydrated_references)

        if self._get_queryset:
            queryset_or_filters = self._get_queryset(model, info, **args)
            if isinstance(queryset_or_filters, mongoengine.QuerySet):
                return queryset_or_filters
            else:
                args.update(queryset_or_filters)
        return model.objects(**args).order_by(self.order_by)

    def default_resolver(self, _root, info, **args):
        args = args or {}

        if _root is not None:
            args["pk__in"] = [r.pk for r in getattr(_root, info.field_name, [])]

        connection_args = {
            "first": args.pop("first", None),
            "last": args.pop("last", None),
            "before": args.pop("before", None),
            "after": args.pop("after", None),
        }

        _id = args.pop('id', None)

        if _id is not None:
            args['pk'] = from_global_id(_id)[-1]

        if callable(getattr(self.model, "objects", None)):
            iterables = self.get_queryset(self.model, info, **args)
            list_length = iterables.count()
        else:
            iterables = []
            list_length = 0

        connection = connection_from_list_slice(
            list_slice=iterables,
            args=connection_args,
            list_length=list_length,
            list_slice_length=list_length,
            connection_type=self.type,
            edge_type=self.type.Edge,
            pageinfo_type=graphene.PageInfo,
        )
        connection.iterable = iterables
        connection.list_length = list_length
        return connection

    def chained_resolver(self, resolver, is_partial, root, info, **args):
        if not bool(args) or not is_partial:
            # XXX: Filter nested args
            resolved = resolver(root, info, **args)
            if resolved is not None:
                return resolved
        return self.default_resolver(root, info, **args)

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
