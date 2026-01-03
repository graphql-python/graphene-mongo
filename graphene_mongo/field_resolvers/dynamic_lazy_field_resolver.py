from collections.abc import Callable
from typing import Optional, Union

from bson import ObjectId
from graphene.utils.str_converters import to_snake_case
from graphene_mongo.utils import (
    ExecutorEnum,
    get_query_fields,
    sync_to_async,
)
from mongoengine import Document


class DynamicLazyFieldResolver:
    @staticmethod
    def __lazy_resolver_common(
        field, registry, executor: ExecutorEnum, root, *args, **kwargs
    ) -> Optional[Union[tuple[Document, set[str], ObjectId], Document]]:
        document = getattr(root, field.name or field.db_name)
        if not document:
            return None
        if document._cached_doc:
            return document._cached_doc

        queried_fields = []
        _type = registry.get_type_for_model(document.document_type, executor=executor)
        filter_args = []
        if _type._meta.filter_fields:
            for key, values in _type._meta.filter_fields.items():
                for each in values:
                    filter_args.append(key + "__" + each)
        for each in get_query_fields(args[0]).keys():
            item = to_snake_case(each)
            if item in document.document_type._fields_ordered + tuple(filter_args):
                queried_fields.append(item)

        only_fields = set((list(_type._meta.required_fields) + queried_fields))

        return document.document_type, only_fields, document.id

    @staticmethod
    def lazy_resolver(field, registry, executor) -> Callable:
        def resolver(root, *args, **kwargs) -> Optional[Document]:
            result = DynamicLazyFieldResolver.__lazy_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return document.objects.no_dereference().only(*only_fields).get(pk=pk)

        return resolver

    @staticmethod
    def lazy_resolver_async(field, registry, executor) -> Callable:
        async def resolver(root, *args, **kwargs) -> Optional[Document]:
            result = DynamicLazyFieldResolver.__lazy_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(result, tuple):
                return result
            document, only_fields, pk = result
            return await sync_to_async(document.objects.no_dereference().only(*only_fields).get)(
                pk=pk
            )

        return resolver
