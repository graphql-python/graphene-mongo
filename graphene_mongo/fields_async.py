from __future__ import absolute_import

from functools import partial
from itertools import filterfalse
from typing import Coroutine

import bson
import graphene
import mongoengine
import pymongo
from bson import DBRef, ObjectId
from graphene import Context
from graphene.relay import ConnectionField
from graphene.utils.str_converters import to_snake_case
from graphql import GraphQLResolveInfo
from graphql_relay import cursor_to_offset, from_global_id
from mongoengine import QuerySet
from promise import Promise
from pymongo.errors import OperationFailure

from . import MongoengineConnectionField
from .registry import get_global_async_registry
from .utils import (
    ExecutorEnum,
    connection_from_iterables,
    find_skip_and_limit,
    get_query_fields,
    has_page_info,
    sync_to_async,
)

PYMONGO_VERSION = tuple(pymongo.version_tuple[:2])


class AsyncMongoengineConnectionField(MongoengineConnectionField):
    def __init__(self, type, *args, **kwargs):
        super(AsyncMongoengineConnectionField, self).__init__(type, *args, **kwargs)

    @property
    def executor(self):
        return ExecutorEnum.ASYNC

    @property
    def type(self):
        from .types_async import AsyncMongoengineObjectType

        _type = super(ConnectionField, self).type
        assert issubclass(
            _type, AsyncMongoengineObjectType
        ), "AsyncMongoengineConnectionField only accepts AsyncMongoengineObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(
            _type.__name__
        )
        return _type._meta.connection

    @property
    def fields(self):
        return super(AsyncMongoengineConnectionField, self).fields

    @property
    def registry(self):
        return getattr(self.node_type._meta, "registry", get_global_async_registry())

    async def default_resolver(self, _root, info, required_fields=None, resolved=None, **args):
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
                        count = await sync_to_async(items.count)(with_limit_and_skip=False)
                    else:
                        count = None
                except OperationFailure:
                    count = await sync_to_async(len)(items)
            else:
                count = len(items)

            skip, limit = find_skip_and_limit(
                first=first, last=last, after=after, before=before, count=count
            )

            if isinstance(items, QuerySet):
                if limit:
                    _base_query: QuerySet = await sync_to_async(items.skip)(skip)
                    items = await sync_to_async(_base_query.limit)(limit)
                    has_next_page = (
                        (
                            await sync_to_async(len)(
                                _base_query.skip(skip + limit).only("id").limit(1)
                            )
                            != 0
                        )
                        if requires_page_info
                        else False
                    )
                elif skip:
                    items = await sync_to_async(items.skip)(skip)
            else:
                if limit:
                    _base_query = items
                    items = items[skip : skip + limit]
                    has_next_page = (
                        (skip + limit) < len(_base_query) if requires_page_info else False
                    )
                elif skip:
                    items = items[skip:]
            iterables = await sync_to_async(list)(items)
            list_length = len(iterables)

        elif callable(getattr(self.model, "objects", None)):
            if (
                _root is None
                or args
                or isinstance(getattr(_root, field_name, []), AsyncMongoengineConnectionField)
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
                    count = await sync_to_async(
                        (mongoengine.get_db()[self.model._get_collection_name()]).count_documents
                    )(args_copy)
                else:
                    count = await sync_to_async(self.model.objects(args_copy).count)()
                if count != 0:
                    skip, limit = find_skip_and_limit(
                        first=first, after=after, last=last, before=before, count=count
                    )
                    iterables = self.get_queryset(
                        self.model, info, required_fields, skip, limit, **args
                    )
                    iterables = await sync_to_async(list)(iterables)
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
                iterables = await sync_to_async(list)(iterables)
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
            iterables = await sync_to_async(list)(iterables)
            list_length = len(iterables)

        if requires_page_info and count:
            has_next_page = (
                True
                if (0 if limit is None else limit) + (0 if skip is None else skip) < count
                else False
            )
        has_previous_page = True if requires_page_info and skip else False

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

    async def chained_resolver(self, resolver, is_partial, root, info, **args):
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
                    if isinstance(self.fields[field], AsyncMongoengineConnectionField)
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
            if isinstance(resolved, Coroutine):
                resolved = await resolved
            if resolved is not None:
                # if isinstance(resolved, Coroutine):
                #     resolved = await resolved
                if isinstance(resolved, list):
                    if resolved == list():
                        return resolved
                    elif not isinstance(resolved[0], DBRef):
                        return resolved
                    else:
                        return await self.default_resolver(root, info, required_fields, **args_copy)
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

                    return await self.default_resolver(
                        root, info, required_fields, resolved=resolved, **args_copy
                    )
                elif isinstance(resolved, Promise):
                    return resolved.value
                else:
                    return await resolved

        return await self.default_resolver(root, info, required_fields, **args)

    @classmethod
    async def connection_resolver(cls, resolver, connection_type, root, info, **args):
        if root:
            for key, value in root.__dict__.items():
                if value:
                    try:
                        setattr(root, key, from_global_id(value)[1])
                    except Exception:
                        pass

        iterable = await resolver(root=root, info=info, **args)

        if isinstance(connection_type, graphene.NonNull):
            connection_type = connection_type.of_type
        on_resolve = partial(cls.resolve_connection, connection_type, args)
        if Promise.is_thenable(iterable):
            iterable = Promise.resolve(iterable).then(on_resolve).value
        return on_resolve(iterable)
