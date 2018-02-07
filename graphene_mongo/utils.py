import inspect
import mongoengine

from collections import OrderedDict
from mongoengine.base.fields import BaseField


def get_model_fields(model, excluding=None):
    if excluding is None:
        excluding = []
    attributes = dict()
    for attr_name in vars(model):
        if attr_name in excluding:
            continue
        attr = getattr(model, attr_name)
        if isinstance(attr, BaseField):
            attributes[attr_name] = attr

    return OrderedDict(sorted(attributes.items()))


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
