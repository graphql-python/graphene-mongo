from __future__ import absolute_import

from collections import OrderedDict
from functools import partial, reduce

from graphene import Field, List
from graphene.relay import ConnectionField
from graphene.relay.connection import PageInfo
from graphql_relay.connection.arrayconnection import connection_from_list_slice
from graphql_relay.node.node import from_global_id
from graphene.types.argument import to_arguments


# noqa
class MongoengineListField(Field):

    def __init__(self, _type, *args, **kwargs):
        super(MongoengineListField, self).__init__(List(_type), *args, **kwargs)

    @property
    def model(self):
        return self.type.of_type._meta.node._meta.model

    # @staticmethod
    # def list_resolver(resolver, root, info, **args):
    #    return maybe_queryset(resolver(root, info, **args))

    def get_resolver(self, parent_resolver):
        return partial(self.list_resolver, parent_resolver)


class MongoengineConnectionField(ConnectionField):

    def __init__(self, type, *args, **kwargs):
        super(MongoengineConnectionField, self).__init__(
            type,
            *args,
            **kwargs
        )

    @property
    def type(self):
        from .types import MongoengineObjectType
        _type = super(ConnectionField, self).type
        assert issubclass(_type, MongoengineObjectType), "MongoengineConnectionField only accepts MongoengineObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(_type.__name__)
        return _type._meta.connection

    @property
    def node_type(self):
        return self.type._meta.node

    @property
    def model(self):
        return self.node_type._meta.model

    @property
    def args(self):
        return to_arguments(
            self._base_args or OrderedDict(), self.default_filter_args
        )

    @args.setter
    def args(self, args):
        self._base_args = args

    @property
    def default_filter_args(self):
        def is_filterable(kv):
            return hasattr(kv[1], '_type') \
                    and callable(getattr(kv[1]._type, '_of_type', None))

        return reduce(
            lambda r, kv: r.update({kv[0]: kv[1]._type._of_type()}) or r if is_filterable(kv) else r,
            self.fields.items(),
            {}
        )

    @property
    def filter_fields(self):
        return self._type._meta.filter_fields

    @property
    def fields(self):
        return self._type._meta.fields

    @classmethod
    def get_query(cls, model, info, **args):

        if not callable(getattr(model, 'objects', None)):
            return []

        objs = model.objects()

        if args:
            first = args.pop('first', None)
            last = args.pop('last', None)
            id = args.pop('id', None)

            if id is not None:
                # https://github.com/graphql-python/graphene/issues/124
                args['pk'] = from_global_id(id)[-1]

            objs = objs.filter(**args)

            if first is not None:
                objs = objs[:first]
            if last is not None:
                objs = objs[:-last]

        return objs

    # noqa
    @classmethod
    def merge_querysets(cls, default_queryset, queryset):
        return queryset & default_queryset

    """
    Notes: Not sure how does this work :(
    """
    @classmethod
    def connection_resolver(cls, resolver, connection, model, root, info, **args):
        iterable = resolver(root, info, **args)
        if not iterable:
            iterable = cls.get_query(model, info, **args)
        _len = len(iterable)
        connection = connection_from_list_slice(
            iterable,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            pageinfo_type=PageInfo,
            edge_type=connection.Edge,
        )
        connection.iterable = iterable
        connection.length = _len
        return connection

    def get_resolver(self, parent_resolver):
        return partial(self.connection_resolver, parent_resolver, self.type, self.model)
