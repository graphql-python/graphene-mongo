import inspect
import mongoengine

from collections import OrderedDict


def get_model_fields(model, excluding=None):
    excluding = excluding or []
    attributes = dict()
    for attr_name, attr in model._fields.items():
        if attr_name in excluding:
            continue
        attributes[attr_name] = attr
    return OrderedDict(sorted(attributes.items()))


def get_model_reference_fields(model, excluding=None):
    excluding = excluding or []
    attributes = dict()
    for attr_name, attr in model._fields.items():
        if attr_name in excluding \
                or not isinstance(attr, mongoengine.fields.ReferenceField):
            continue
        attributes[attr_name] = attr
    return attributes


def is_valid_mongoengine_model(model):
    return inspect.isclass(model) and (
        issubclass(model, mongoengine.Document) or issubclass(model, mongoengine.EmbeddedDocument)
    )


def import_single_dispatch():
    try:
        from functools import singledispatch
    except ImportError:
        singledispatch = None

    if not singledispatch:
        try:
            from singledispatch import singledispatch
        except ImportError:
            pass

    if not singledispatch:
        raise Exception(
            "It seems your python version does not include "
            "functools.singledispatch. Please install the 'singledispatch' "
            "package. More information here: "
            "https://pypi.python.org/pypi/singledispatch"
        )

    return singledispatch


# noqa
def get_type_for_document(schema, document):
    types = schema.types.values()
    for _type in types:
        type_document = hasattr(_type, '_meta') and getattr(
            _type._meta, 'document', None)
        if document == type_document:
            return _type
