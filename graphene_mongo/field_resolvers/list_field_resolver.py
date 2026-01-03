import asyncio
from asyncio import Future, Task
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from mongoengine.base import LazyReference, get_document


class ListFieldResolver:
    @staticmethod
    def __get_reference_objects_common(
        registry,
        model,
        executor: ExecutorEnum,
        object_id_list: list[ObjectId],
        queried_fields: dict,
    ) -> tuple[Document, set[str], list[ObjectId]]:
        from graphene_mongo.converter import convert_mongoengine_field

        document = get_document(model)
        document_field = mongoengine.ReferenceField(document)
        document_field = convert_mongoengine_field(document_field, registry, executor)
        document_field_type = document_field.get_type().type
        _queried_fields = list()
        filter_args = list()
        if document_field_type._meta.filter_fields:
            for key, values in document_field_type._meta.filter_fields.items():
                for each in values:
                    filter_args.append(key + "__" + each)
        for each in queried_fields:
            item = to_snake_case(each)
            if item in document._fields_ordered + tuple(filter_args):
                _queried_fields.append(item)

        only_fields = set(list(document_field_type._meta.required_fields) + _queried_fields)
        return document, only_fields, object_id_list

    # ======================= DB CALLS =======================
    @staticmethod
    def __get_reference_objects(
        registry,
        model,
        executor: ExecutorEnum,
        object_id_list: list[ObjectId],
        queried_fields: dict,
    ):
        document, only_fields, document_ids = ListFieldResolver.__get_reference_objects_common(
            registry, model, executor, object_id_list, queried_fields
        )
        return document.objects().no_dereference().only(*only_fields).filter(pk__in=document_ids)

    @staticmethod
    async def __get_reference_objects_async(
        registry,
        model,
        executor: ExecutorEnum,
        object_id_list: list[ObjectId],
        queried_fields: dict,
    ):
        document, only_fields, document_ids = ListFieldResolver.__get_reference_objects_common(
            registry, model, executor, object_id_list, queried_fields
        )
        return await sync_to_async(list)(
            document.objects().no_dereference().only(*only_fields).filter(pk__in=document_ids)
        )

    # ======================= DB CALLS: END =======================

    @staticmethod
    def __get_non_querying_object(model, object_id_list) -> list[Document]:
        model = get_document(model)
        return [model(pk=each) for each in object_id_list]

    @staticmethod
    async def __get_non_querying_object_async(model, object_id_list) -> list[Document]:
        return ListFieldResolver.__get_non_querying_object(model, object_id_list)

    @staticmethod
    def __build_results(
        result: list[Document], to_resolve_object_ids: list[ObjectId]
    ) -> list[Document]:
        result_object: dict[ObjectId, Document] = {}
        for items in result:
            for item in items:
                result_object[item.id] = item
        return [result_object[each] for each in to_resolve_object_ids]

    # ======================= Main Logic =======================

    @staticmethod
    def __reference_resolver_common(
        field, registry, executor: ExecutorEnum, root, *args, **kwargs
    ) -> Optional[tuple[Union[list[Task], list[Document]], list[ObjectId]]]:
        to_resolve = getattr(root, field.name or field.db_name)
        if not to_resolve:
            return None

        choice_to_resolve = dict()
        registry_string_map = (
            registry._registry_string_map
            if executor == ExecutorEnum.SYNC
            else registry._registry_async_string_map
        )
        querying_union_types = get_queried_union_types(
            info=args[0], valid_gql_types=registry_string_map.keys()
        )
        to_resolve_models = dict()
        for each, queried_fields in querying_union_types.items():
            to_resolve_models[registry_string_map[each]] = queried_fields
        to_resolve_object_ids: list[ObjectId] = list()
        for each in to_resolve:
            if isinstance(each, LazyReference):
                to_resolve_object_ids.append(each.pk)
                model = each.document_type._class_name
                if model not in choice_to_resolve:
                    choice_to_resolve[model] = list()
                choice_to_resolve[model].append(each.pk)
            else:
                to_resolve_object_ids.append(each["_ref"].id)
                if each["_cls"] not in choice_to_resolve:
                    choice_to_resolve[each["_cls"]] = list()
                choice_to_resolve[each["_cls"]].append(each["_ref"].id)

        if executor == ExecutorEnum.SYNC:
            pool = ThreadPoolExecutor(5)
            futures: list[Future] = list()
            for model, object_id_list in choice_to_resolve.items():
                if model in to_resolve_models:
                    queried_fields = to_resolve_models[model]
                    futures.append(
                        pool.submit(
                            ListFieldResolver.__get_reference_objects,
                            *(registry, model, executor, object_id_list, queried_fields),
                        )
                    )
                else:
                    futures.append(
                        pool.submit(
                            ListFieldResolver.__get_non_querying_object,
                            *(model, object_id_list),
                        )
                    )
            result = [future.result() for future in as_completed(futures)]
            return result, to_resolve_object_ids
        else:
            loop = asyncio.get_event_loop()
            tasks: list[Task] = []
            for model, object_id_list in choice_to_resolve.items():
                if model in to_resolve_models:
                    queried_fields = to_resolve_models[model]
                    task = loop.create_task(
                        ListFieldResolver.__get_reference_objects_async(
                            registry, model, executor, object_id_list, queried_fields
                        )
                    )
                else:
                    task = loop.create_task(
                        ListFieldResolver.__get_non_querying_object_async(model, object_id_list)
                    )
                tasks.append(task)
            return tasks, to_resolve_object_ids

    @staticmethod
    def reference_resolver(field, registry, executor) -> Callable:
        def resolver(root, *args, **kwargs) -> Optional[list[Document]]:
            resolver_result = ListFieldResolver.__reference_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(resolver_result, tuple):
                return resolver_result
            result, to_resolve_object_ids = resolver_result
            return ListFieldResolver.__build_results(result, to_resolve_object_ids)

        return resolver

    @staticmethod
    def reference_resolver_async(field, registry, executor) -> Callable:
        async def resolver(root, *args, **kwargs) -> Optional[list[Document]]:
            resolver_result = ListFieldResolver.__reference_resolver_common(
                field, registry, executor, root, *args, **kwargs
            )
            if not isinstance(resolver_result, tuple):
                return resolver_result
            tasks, to_resolve_object_ids = resolver_result
            result: list[Document] = await asyncio.gather(*tasks)
            return ListFieldResolver.__build_results(result, to_resolve_object_ids)

        return resolver

    # ======================= Main Logic: END =======================
