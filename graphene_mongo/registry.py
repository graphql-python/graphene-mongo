class Registry(object):
    def __init__(self):
        self._registry = {}

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

        # Rescan all fields
        for model, cls in self._registry.items():
            cls.rescan_fields()

    def get_type_for_model(self, model):
        return self._registry.get(model)


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


def reset_inputs_registry():
    global inputs_registry
    inputs_registry = None


def reset_global_registry():
    global registry
    registry = None
