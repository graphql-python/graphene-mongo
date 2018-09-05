from __future__ import absolute_import

from collections import OrderedDict
from functools import partial, reduce

from graphene import Field, List
from graphene.relay import ConnectionField
from graphene.relay.connection import PageInfo
from graphql_relay.connection.arrayconnection import connection_from_list_slice
from graphql_relay.node.node import from_global_id
from graphene.types.argument import to_arguments
from graphene.types.dynamic import Dynamic
from graphene.types.structures import Structure

from .utils import get_model_reference_fields


# noqa
class MongoengineListField(Field):

    def __init__(self, _type, *args, **kwargs):
        super(MongoengineListField, self).__init__(
            List(_type), *args, **kwargs)

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
        assert issubclass(
            _type, MongoengineObjectType), "MongoengineConnectionField only accepts MongoengineObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(
            _type.__name__)
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
            self._base_args or OrderedDict(),
            dict(self.field_args, **self.reference_args)
        )

    @args.setter
    def args(self, args):
        self._base_args = args

    @property
    def field_args(self):
        def is_filterable(v):
            return not isinstance(v, (ConnectionField, Dynamic))

        def get_type(v):
            if isinstance(v.type, Structure):
                return v.type.of_type()
            return v.type()

        return {k: get_type(v) for k, v in self.fields.items()
                if is_filterable(v)}

    @property
    def reference_args(self):
        def get_reference_field(r, kv):
            if callable(getattr(kv[1], 'get_type', None)):
                node = kv[1].get_type()._type._meta
                r.update({kv[0]: node.fields['id']._type.of_type()})
            return r
        return reduce(get_reference_field, self.fields.items(), {})

    @property
    def fields(self):
        return self._type._meta.fields

    @classmethod
    def get_query(cls, model, info, **args):

        if not callable(getattr(model, 'objects', None)):
            return [], 0

        objs = model.objects()

        if args:
            reference_fields = get_model_reference_fields(model)
            reference_args = {}
            for arg_name, arg in args.copy().items():
                if arg_name in reference_fields:
                    reference_model = model._fields[arg_name]
                    pk = from_global_id(args.pop(arg_name))[-1]
                    reference_obj = reference_model.document_type_obj.objects(pk=pk).get()
                    reference_args[arg_name] = reference_obj

            args.update(reference_args)
            first = args.pop('first', None)
            last = args.pop('last', None)
            id = args.pop('id', None)
            before = args.pop('before', None)
            after = args.pop('after', None)

            if id is not None:
                # https://github.com/graphql-python/graphene/issues/124
                args['pk'] = from_global_id(id)[-1]

            objs = objs.filter(**args)

            # https://github.com/graphql-python/graphene-mongo/issues/21
            if after is not None:
                _after = int(from_global_id(after)[-1])
                objs = objs[_after:]

            if before is not None:
                _before = int(from_global_id(before)[-1])
                objs = objs[:_before]

            list_length = objs.count()

            if first is not None:
                objs = objs[:first]
            if last is not None:
                # https://github.com/graphql-python/graphene-mongo/issues/20
                objs = objs[max(0, list_length - last):]
        else:
            list_length = objs.count()

        return objs, list_length

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
            iterable, _len = cls.get_query(model, info, **args)

            if root:
                # If we have a root, we must be at least 1 layer in, right?
                _len = 0
        else:
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
