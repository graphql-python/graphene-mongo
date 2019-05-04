import graphene
import mongoengine

from collections import OrderedDict
from graphene.relay import Connection, Node
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from graphene_mongo import MongoengineConnectionField
from .converter import convert_mongoengine_field
from .registry import Registry, get_global_registry
from .utils import (get_model_fields, is_valid_mongoengine_model)


def construct_fields(model, registry, only_fields, exclude_fields):
    """
    Args:
        model (mongoengine.Document):
        registry (graphene_mongo.registry.Registry):
        only_fields ([str]):
        exclude_fields ([str]):

    Returns:
        (OrderedDict, OrderedDict): coverted fields and self reference fields.

    """
    _model_fields = get_model_fields(model)
    fields = OrderedDict()
    self_referenced = OrderedDict()
    for name, field in _model_fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields
        if is_not_in_only or is_excluded:
            # We skip this field if we specify only_fields and is not
            # in there. Or when we exclude this field in exclude_fields
            continue
        if isinstance(field, mongoengine.ListField):
            # Take care of list of self-reference.
            document_type_obj = field.field.__dict__.get('document_type_obj', None)
            if document_type_obj == model._class_name \
                    or isinstance(document_type_obj, model) \
                    or document_type_obj == model:
                self_referenced[name] = field
                continue
        converted = convert_mongoengine_field(field, registry)
        if not converted:
            continue
        fields[name] = converted

    return fields, self_referenced


def construct_self_referenced_fields(self_referenced, registry):
    fields = OrderedDict()
    for name, field in self_referenced.items():
        converted = convert_mongoengine_field(field, registry)
        if not converted:
            continue
        fields[name] = converted

    return fields


class MongoengineObjectTypeOptions(ObjectTypeOptions):

    model = None  # type: Model
    registry = None  # type: Registry
    only_fields = ()
    exclude_fields = ()
    filter_fields = ()
    connection = None  # type: Type[Connection]
    connection_class = None
    use_connection = None
    connection_field_class = None
    interfaces = ()


class MongoengineObjectType(ObjectType):

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, registry=None, skip_registry=False,
                                    only_fields=(), exclude_fields=(), filter_fields=None,
                                    connection=None, connection_class=None, use_connection=None,
                                    connection_field_class=None, interfaces=(), _meta=None,
                                    **options):

        if not _meta:
            _meta = MongoengineObjectTypeOptions(cls)
            _meta.model = model
            _meta.registry = registry
            _meta.filter_fields = filter_fields
            _meta.connection = connection
            _meta.connection_class = connection_class
            _meta.use_connection = use_connection
            _meta.connection_field_class = connection_field_class
            _meta.interfaces = interfaces
            # Save them for later
            _meta.only_fields = only_fields
            _meta.exclude_fields = exclude_fields

        assert is_valid_mongoengine_model(_meta.model), (
            'The attribute model in {}.Meta must be a valid Mongoengine Model. '
            'Received "{}" instead.'
        ).format(cls.__name__, type(_meta.model))

        if not _meta.registry:
            _meta.registry = get_global_registry()

        assert isinstance(_meta.registry, Registry), (
            'The attribute registry in {}.Meta needs to be an instance of '
            'Registry, received "{}".'
        ).format(cls.__name__, _meta.registry)
        converted_fields, self_referenced = construct_fields(
            _meta.model, _meta.registry, _meta.only_fields,
            _meta.exclude_fields
        )
        mongoengine_fields = yank_fields_from_attrs(converted_fields, _as=graphene.Field)
        _meta.fields = mongoengine_fields

        if _meta.use_connection is None and _meta.interfaces:
            _meta.use_connection = any((issubclass(interface, Node)
                                        for interface in _meta.interfaces))

        if _meta.use_connection and not _meta.connection:
            # We create the connection automatically
            if not _meta.connection_class:
                _meta.connection_class = Connection

            _meta.connection = _meta.connection_class.create_type(
                '{}Connection'.format(cls.__name__), node=cls)
        if _meta.connection is not None:
            assert issubclass(_meta.connection, Connection), (
                'The attribute connection in {}.Meta must be of type Connection. '
                'Received "{}" instead.'
            ).format(cls.__name__, type(_meta.connection))

        if _meta.connection_field_class is not None:
            assert issubclass(_meta.connection_field_class, graphene.ConnectionField), (
                'The attribute connection_field_class in {}.Meta must be of type graphene.ConnectionField. '
                'Received "{}" instead.'
            ).format(cls.__name__, type(_meta.connection_field_class))
        else:
            _meta.connection_field_class = MongoengineConnectionField

        super(MongoengineObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, interfaces=_meta.interfaces, **options
        )

        if not skip_registry:
            _meta.registry.register(cls)
            # Notes: Take care list of self-reference fields.
            converted_fields = construct_self_referenced_fields(self_referenced, _meta.registry)
            if converted_fields:
                mongoengine_fields = yank_fields_from_attrs(converted_fields, _as=graphene.Field)
                cls._meta.fields.update(mongoengine_fields)
                _meta.registry.register(cls)

    @classmethod
    def rescan_fields(cls):
        """Attempts to rescan fields and will insert any not converted initially"""

        converted_fields, self_referenced = construct_fields(
            cls._meta.model, cls._meta.registry,
            cls._meta.only_fields, cls._meta.exclude_fields
        )

        mongoengine_fields = yank_fields_from_attrs(converted_fields, _as=graphene.Field)

        # The initial scan should take precidence
        for field in mongoengine_fields:
            if field not in cls._meta.fields:
                cls._meta.fields.update({field: mongoengine_fields[field]})
        # Self-referenced fields can't change between scans!


    # noqa
    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True
        if not is_valid_mongoengine_model(type(root)):
            raise Exception((
                'Received incompatible instance "{}".'
            ).format(root))
        return isinstance(root, cls._meta.model)

    @classmethod
    def get_node(cls, info, id):
        return cls._meta.model.objects.get(pk=id)

    def resolve_id(self, info):
        return str(self.id)

    # @classmethod
    # def get_connection(cls):
    #     return connection_for_type(cls)
