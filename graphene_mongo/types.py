from collections import OrderedDict

import graphene
import mongoengine
from graphene.relay import Connection, Node
from graphene.types.inputobjecttype import InputObjectType, InputObjectTypeOptions
from graphene.types.interface import Interface, InterfaceOptions
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs
from graphene.utils.str_converters import to_snake_case

from graphene_mongo import MongoengineConnectionField
from .converter import convert_mongoengine_field
from .registry import Registry, get_global_registry, get_inputs_registry
from .utils import (
    ExecutorEnum,
    get_model_fields,
    get_query_fields,
    is_valid_mongoengine_model,
    sync_to_async,
)


def construct_fields(
    model,
    registry,
    only_fields,
    exclude_fields,
    non_required_fields,
    executor: ExecutorEnum = ExecutorEnum.SYNC,
):
    """
    Args:
        model (mongoengine.Document):
        registry (.registry.Registry):
        only_fields ([str]):
        exclude_fields ([str]):
        executor : ExecutorEnum

    Returns:
        (OrderedDict, OrderedDict): converted fields and self reference fields.

    """
    _model_fields = get_model_fields(model)
    fields = OrderedDict()
    self_referenced = OrderedDict()
    for name, field in _model_fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields
        if is_not_in_only or is_excluded:
            # We skip this field if we specify required_fields and is not
            # in there. Or when we exclude this field in exclude_fields
            continue
        if isinstance(field, mongoengine.ListField):
            if not field.field:
                continue
            # Take care of list of self-reference.
            document_type_obj = field.field.__dict__.get("document_type_obj", None)
            if (
                document_type_obj == model._class_name
                or isinstance(document_type_obj, model)
                or document_type_obj == model
            ):
                self_referenced[name] = field
                continue
        converted = convert_mongoengine_field(field, registry, executor)
        if not converted:
            continue
        else:
            if name in non_required_fields and "required" in converted.kwargs:
                converted.kwargs["required"] = False
        fields[name] = converted

    return fields, self_referenced


def construct_self_referenced_fields(self_referenced, registry, executor=ExecutorEnum.SYNC):
    fields = OrderedDict()
    for name, field in self_referenced.items():
        converted = convert_mongoengine_field(field, registry, executor)
        if not converted:
            continue
        fields[name] = converted

    return fields


def create_graphene_generic_class(object_type, option_type):
    class MongoengineGenericObjectTypeOptions(option_type):
        model = None
        registry = None  # type: Registry
        connection = None
        filter_fields = ()
        non_required_fields = ()
        order_by = None

    class GrapheneMongoengineGenericType(object_type):
        @classmethod
        def __init_subclass_with_meta__(
            cls,
            model=None,
            registry=None,
            skip_registry=False,
            only_fields=(),
            required_fields=(),
            exclude_fields=(),
            non_required_fields=(),
            filter_fields=None,
            non_filter_fields=(),
            connection=None,
            connection_class=None,
            use_connection=None,
            connection_field_class=None,
            interfaces=(),
            _meta=None,
            order_by=None,
            **options,
        ):
            assert is_valid_mongoengine_model(model), (
                "The attribute model in {}.Meta must be a valid Mongoengine Model. "
                'Received "{}" instead.'
            ).format(cls.__name__, type(model))

            if not registry:
                # input objects shall be registred in a separated registry
                if issubclass(cls, InputObjectType):
                    registry = get_inputs_registry()
                else:
                    registry = get_global_registry()

            assert isinstance(registry, Registry), (
                "The attribute registry in {}.Meta needs to be an instance of "
                'Registry({}), received "{}".'
            ).format(object_type, cls.__name__, registry)
            converted_fields, self_referenced = construct_fields(
                model, registry, only_fields, exclude_fields, non_required_fields
            )
            mongoengine_fields = yank_fields_from_attrs(converted_fields, _as=graphene.Field)
            if use_connection is None and interfaces:
                use_connection = any((issubclass(interface, Node) for interface in interfaces))

            if use_connection and not connection:
                # We create the connection automatically
                if not connection_class:
                    connection_class = Connection

                connection = connection_class.create_type(
                    "{}Connection".format(options.get("name") or cls.__name__), node=cls
                )

            if connection is not None:
                assert issubclass(connection, Connection), (
                    "The attribute connection in {}.Meta must be of type Connection. "
                    'Received "{}" instead.'
                ).format(cls.__name__, type(connection))

            if connection_field_class is not None:
                assert issubclass(connection_field_class, graphene.ConnectionField), (
                    "The attribute connection_field_class in {}.Meta must be of type graphene.ConnectionField. "
                    'Received "{}" instead.'
                ).format(cls.__name__, type(connection_field_class))
            else:
                connection_field_class = MongoengineConnectionField

            if _meta:
                assert isinstance(_meta, MongoengineGenericObjectTypeOptions), (
                    "_meta must be an instance of MongoengineGenericObjectTypeOptions, "
                    "received {}"
                ).format(_meta.__class__)
            else:
                _meta = MongoengineGenericObjectTypeOptions(option_type)

            _meta.model = model
            _meta.registry = registry
            _meta.fields = mongoengine_fields
            _meta.filter_fields = filter_fields
            _meta.non_filter_fields = non_filter_fields
            _meta.connection = connection
            _meta.connection_field_class = connection_field_class
            # Save them for later
            _meta.only_fields = only_fields
            _meta.required_fields = required_fields
            _meta.exclude_fields = exclude_fields
            _meta.non_required_fields = non_required_fields
            _meta.order_by = order_by

            super(GrapheneMongoengineGenericType, cls).__init_subclass_with_meta__(
                _meta=_meta, interfaces=interfaces, **options
            )

            if not skip_registry:
                registry.register(cls)
                # Notes: Take care list of self-reference fields.
                converted_fields = construct_self_referenced_fields(self_referenced, registry)
                if converted_fields:
                    mongoengine_fields = yank_fields_from_attrs(
                        converted_fields, _as=graphene.Field
                    )
                    cls._meta.fields.update(mongoengine_fields)
                    registry.register(cls)

        @classmethod
        def rescan_fields(cls):
            """Attempts to rescan fields and will insert any not converted initially"""

            converted_fields, self_referenced = construct_fields(
                cls._meta.model,
                cls._meta.registry,
                cls._meta.only_fields,
                cls._meta.exclude_fields,
                cls._meta.non_required_fields,
            )

            mongoengine_fields = yank_fields_from_attrs(converted_fields, _as=graphene.Field)

            # The initial scan should take precedence
            for field in mongoengine_fields:
                if field not in cls._meta.fields:
                    cls._meta.fields.update({field: mongoengine_fields[field]})
            # Self-referenced fields can't change between scans!

        @classmethod
        def is_type_of(cls, root, info):
            if isinstance(root, cls):
                return True
            # XXX: Take care FileField
            if isinstance(root, mongoengine.GridFSProxy):
                return True
            if not is_valid_mongoengine_model(type(root)):
                raise Exception(('Received incompatible instance "{}".').format(root))
            return isinstance(root, cls._meta.model)

        @classmethod
        async def get_node(cls, info, id):
            required_fields = list()
            for field in cls._meta.required_fields:
                if field in cls._meta.model._fields_ordered:
                    required_fields.append(field)
            queried_fields = get_query_fields(info)
            if cls._meta.name in queried_fields:
                queried_fields = queried_fields[cls._meta.name]
            for field in queried_fields:
                if to_snake_case(field) in cls._meta.model._fields_ordered:
                    required_fields.append(to_snake_case(field))
            required_fields = list(set(required_fields))
            return await sync_to_async(
                cls._meta.model.objects.no_dereference().only(*required_fields).get,
            )(pk=id)

        def resolve_id(self, info):
            return str(self.id)

    return GrapheneMongoengineGenericType, MongoengineGenericObjectTypeOptions


MongoengineObjectType, MongoengineObjectTypeOptions = create_graphene_generic_class(
    ObjectType, ObjectTypeOptions
)
MongoengineInterfaceType, MongoengineInterfaceTypeOptions = create_graphene_generic_class(
    Interface, InterfaceOptions
)
MongoengineInputType, MongoengineInputTypeOptions = create_graphene_generic_class(
    InputObjectType, InputObjectTypeOptions
)

GrapheneMongoengineObjectTypes = (
    MongoengineObjectType,
    MongoengineInputType,
    MongoengineInterfaceType,
)
