import graphene
import mongoengine
from graphene import InputObjectType
from graphene.relay import Connection, Node
from graphene.types.interface import Interface, InterfaceOptions
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs
from graphene.utils.str_converters import to_snake_case

from graphene_mongo import AsyncMongoengineConnectionField
from .registry import Registry, get_global_async_registry, get_inputs_async_registry
from .types import construct_fields, construct_self_referenced_fields
from .utils import ExecutorEnum, get_query_fields, is_valid_mongoengine_model, sync_to_async


def create_graphene_generic_class_async(object_type, option_type):
    class AsyncMongoengineGenericObjectTypeOptions(option_type):
        model = None
        registry = None  # type: Registry
        connection = None
        filter_fields = ()
        non_required_fields = ()
        order_by = None

    class AsyncGrapheneMongoengineGenericType(object_type):
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
                    registry = get_inputs_async_registry()
                else:
                    registry = get_global_async_registry()

            assert isinstance(registry, Registry), (
                "The attribute registry in {}.Meta needs to be an instance of "
                'Registry({}), received "{}".'
            ).format(object_type, cls.__name__, registry)
            converted_fields, self_referenced = construct_fields(
                model,
                registry,
                only_fields,
                exclude_fields,
                non_required_fields,
                ExecutorEnum.ASYNC,
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
                connection_field_class = AsyncMongoengineConnectionField

            if _meta:
                assert isinstance(_meta, AsyncMongoengineGenericObjectTypeOptions), (
                    "_meta must be an instance of AsyncMongoengineGenericObjectTypeOptions, "
                    "received {}"
                ).format(_meta.__class__)
            else:
                _meta = AsyncMongoengineGenericObjectTypeOptions(option_type)

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

            super(AsyncGrapheneMongoengineGenericType, cls).__init_subclass_with_meta__(
                _meta=_meta, interfaces=interfaces, **options
            )

            if not skip_registry:
                registry.register(cls)
                # Notes: Take care list of self-reference fields.
                converted_fields = construct_self_referenced_fields(
                    self_referenced, registry, ExecutorEnum.ASYNC
                )
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
                ExecutorEnum.ASYNC,
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
                cls._meta.model.objects.no_dereference().only(*required_fields).get
            )(pk=id)

        def resolve_id(self, info):
            return str(self.id)

    return AsyncGrapheneMongoengineGenericType, AsyncMongoengineGenericObjectTypeOptions


(
    AsyncMongoengineObjectType,
    AsyncMongoengineObjectTypeOptions,
) = create_graphene_generic_class_async(ObjectType, ObjectTypeOptions)

(
    AsyncMongoengineInterfaceType,
    MongoengineInterfaceTypeOptions,
) = create_graphene_generic_class_async(Interface, InterfaceOptions)

AsyncGrapheneMongoengineObjectTypes = (
    AsyncMongoengineObjectType,
    AsyncMongoengineInterfaceType,
)
