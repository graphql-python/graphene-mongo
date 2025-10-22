from collections.abc import Callable
from typing import Optional, Union

from bson import ObjectId
from graphene.utils.str_converters import to_snake_case
from graphene_mongo.utils import (
    ExecutorEnum,
    get_queried_union_types,
    sync_to_async,
)
import mongoengine
from mongoengine import Document
from mongoengine.base import get_document


class UnionFieldResolver:
    @staticmethod
    def __reference_resolver_common(
        field, registry, executor: ExecutorEnum, root, *args, **kwargs
    ) -> Optional[Union[tuple[Document, set[str], ObjectId], Document]]:
        from graphene_mongo.converter import convert_mongoengine_field

        de_referenced = getattr(root, field.name or field.db_name)
        if not de_referenced:
            return None

        document = get_document(de_referenced["_cls"])
        document_id = de_referenced["_ref"].id
        document_field = mongoengine.ReferenceField(document)
        document_field = convert_mongoengine_field(document_field, registry, executor=executor)
        _type = document_field.get_type().type
        filter_args = list()
        if _type._meta.filter_fields:
            for key, values in _type._meta.filter_fields.items():
                for each in values:
                    filter_args.append(key + "__" + each)

        registry_string_map = (
            registry._registry_string_map
            if executor == ExecutorEnum.SYNC
            else registry._registry_async_string_map
        )
        querying_union_types = get_queried_union_types(
            info=args[0], valid_gql_types=registry_string_map.keys()
        )

        if _type.__name__ in querying_union_types:
            queried_fields = list()
            for each in querying_union_types[_type._meta.name].keys():
                item = to_snake_case(each)
                if item in document._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)

            only_fields = set(list(_type._meta.required_fields) + queried_fields)

            return document, only_fields, document_id

        return document(id=document_id)

    @staticmethod
    def __lazy_reference_resolver_common(
        field, registry, executor: ExecutorEnum, root, *args, **kwargs
    ) -> Optional[Union[tuple[Document, set[str], ObjectId], Document]]:
        document = getattr(root, field.name or field.db_name)

        if not document:
            return None

        if document._cached_doc:
            return document._cached_doc

        document_id = document.pk
        queried_fields = list()
        document_field_type = registry.get_type_for_model(document.document_type, executor=executor)
        querying_union_types = get_queried_union_types(
            info=args[0], valid_gql_types=registry._registry_string_map.keys()
        )
        filter_args = list()
        if document_field_type._meta.filter_fields:
            for key, values in document_field_type._meta.filter_fields.items():
                for each in values:
                    filter_args.append(key + "__" + each)
        if document_field_type._meta.name in querying_union_types:
            for each in querying_union_types[document_field_type._meta.name].keys():
                item = to_snake_case(each)
                if item in document.document_type._fields_ordered + tuple(filter_args):
                    queried_fields.append(item)
            _type = registry.get_type_for_model(document.document_type, executor=executor)
            only_fields = set(list(_type._meta.required_fields) + queried_fields)

            return document.document_type, only_fields, document_id

        return document.document_type(id=document.pk)

    @staticmethod
    def resolver(field, registry, executor) -> Callable:
        def resolver(root, *args, **kwargs) -> Optional[Document]:
            resolver_fun = (
                UnionFieldResolver.__reference_resolver_common
                if isinstance(field, mongoengine.GenericReferenceField)
                else UnionFieldResolver.__lazy_reference_resolver_common
            )
            result = resolver_fun(field, registry, executor, root, *args, **kwargs)
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return document.objects.no_dereference().only(*only_fields).get(pk=pk)

        return resolver

    @staticmethod
    def resolver_async(field, registry, executor) -> Callable:
        async def resolver(root, *args, **kwargs) -> Optional[Document]:
            resolver_fun = (
                UnionFieldResolver.__reference_resolver_common
                if isinstance(field, mongoengine.GenericReferenceField)
                else UnionFieldResolver.__lazy_reference_resolver_common
            )
            result = resolver_fun(field, registry, executor, root, *args, **kwargs)
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return await sync_to_async(document.objects.no_dereference().only(*only_fields).get)(
                pk=pk
            )

        return resolver
