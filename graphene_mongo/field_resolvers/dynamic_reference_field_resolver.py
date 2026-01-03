from collections.abc import Callable
from typing import Optional, Union

from bson import ObjectId
from graphene.utils.str_converters import to_snake_case
from graphene_mongo.utils import (
    ExecutorEnum,
    get_query_fields,
    sync_to_async,
)
from mongoengine import Document, ReferenceField


class DynamicReferenceFieldResolver:
    @staticmethod
    def __reference_resolver_common(
        field, registry, executor: ExecutorEnum, root, *args, **kwargs
    ) -> Optional[Union[tuple[Document, set[str], ObjectId], Document]]:
        document = root._data.get(field.name or field.db_name, None)
        if not document:
            return None

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

        fields_to_fetch = set(list(_type._meta.required_fields) + queried_fields)
        if isinstance(document, field.document_type) and all(
            document._data[_field] is not None for _field in fields_to_fetch
        ):
            return document  # Data is already fetched

        document_id = (
            document.id
            if isinstance(field, ReferenceField)
            else getattr(root, field.name or field.db_name)
        )
        return field.document_type, fields_to_fetch, document_id

    @staticmethod
    def reference_resolver(field, registry, executor) -> Callable:
        def resolver(root, *args, **kwargs) -> Optional[Document]:
            result = DynamicReferenceFieldResolver.__reference_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return document.objects.no_dereference().only(*only_fields).get(pk=pk)

        return resolver

    @staticmethod
    def reference_resolver_async(field, registry, executor) -> Callable:
        async def resolver(root, *args, **kwargs) -> Optional[Document]:
            result = DynamicReferenceFieldResolver.__reference_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return await sync_to_async(document.objects.no_dereference().only(*only_fields).get)(
                pk=pk
            )

        return resolver
