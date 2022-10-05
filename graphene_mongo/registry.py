from graphene import Enum


class Registry(object):
    def __init__(self):
        self._registry = {}
        self._registry_string_map = {}
        self._registry_enum = {}

    def register(self, cls):
        from .types import GrapheneMongoengineObjectTypes

        assert issubclass(
            cls,
            GrapheneMongoengineObjectTypes
        ), 'Only Mongoengine object types can be registered, received "{}"'.format(
            cls.__name__
        )
        assert cls._meta.registry == self, "Registry for a Model have to match."
        self._registry[cls._meta.model] = cls
        self._registry_string_map[cls.__name__] = cls._meta.model.__name__

        # Rescan all fields
        for model, cls in self._registry.items():
            cls.rescan_fields()

    def register_enum(self, cls):
        from enum import EnumMeta
        assert type(cls) == EnumMeta, 'Only EnumMeta can be registered, received "{}"'.format(
            cls.__name__
        )
        if not cls.__name__.endswith('Enum'):
            name = cls.__name__ + 'Enum'
        else:
            name = cls.__name__
        cls.__name__ = name
        self._registry_enum[cls] = Enum.from_enum(cls)

    def get_type_for_model(self, model):
        return self._registry.get(model)

    def check_enum_already_exist(self, cls):
        return cls in self._registry_enum

    def get_type_for_enum(self, cls):
        return self._registry_enum.get(cls)


registry = None
inputs_registry = None


def get_inputs_registry():
    global inputs_registry
    if not inputs_registry:
        inputs_registry = Registry()
    return inputs_registry


def get_global_registry():
    global registry
    if not registry:
        registry = Registry()
    return registry


def reset_global_registry():
    global registry
    global inputs_registry
    registry = None
    inputs_registry = None
