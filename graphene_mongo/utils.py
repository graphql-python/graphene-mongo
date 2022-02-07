from __future__ import unicode_literals

import inspect
from collections import OrderedDict

import mongoengine
from graphene import Node
from graphene.utils.trim_docstring import trim_docstring
# from graphql.utils.ast_to_dict import ast_to_dict
from graphql import FieldNode
from graphql_relay.connection.array_connection import offset_to_cursor


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
        if attr_name in excluding or not isinstance(
                attr,
                (mongoengine.fields.ReferenceField, mongoengine.fields.LazyReferenceField),
        ):
            continue
        attributes[attr_name] = attr
    return attributes


def is_valid_mongoengine_model(model):
    return inspect.isclass(model) and (
            issubclass(model, mongoengine.Document)
            or issubclass(model, mongoengine.EmbeddedDocument)
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
        type_document = hasattr(_type, "_meta") and getattr(
            _type._meta, "document", None
        )
        if document == type_document:
            return _type


def get_field_description(field, registry=None):
    """
    Common metadata includes verbose_name and help_text.

    http://docs.mongoengine.org/apireference.html#fields
    """
    parts = []
    if hasattr(field, "document_type"):
        doc = trim_docstring(field.document_type.__doc__)
        if doc:
            parts.append(doc)
    if hasattr(field, "verbose_name"):
        parts.append(field.verbose_name.title())
    if hasattr(field, "help_text"):
        parts.append(field.help_text)
    if field.db_field != field.name:
        name_format = "(%s)" if parts else "%s"
        parts.append(name_format % field.db_field)

    return "\n".join(parts)


def get_node_from_global_id(node, info, global_id):
    try:
        for interface in node._meta.interfaces:
            if issubclass(interface, Node):
                return interface.get_node_from_global_id(info, global_id)
    except AttributeError:
        return Node.get_node_from_global_id(info, global_id)


def collect_query_fields(node, fragments):
    """Recursively collects fields from the AST

    Args:
        node (dict): A node in the AST
        fragments (dict): Fragment definitions

    Returns:
        A dict mapping each field found, along with their sub fields.
        {
            'name': {},
            'image': {
                        'id': {},
                        'name': {},
                        'description': {}
                    },
            'slug': {}
        }
    """

    field = {}
    selection_set = None
    if type(node) == dict:
        selection_set = node.get('selection_set')
    else:
        selection_set = node.selection_set
    if selection_set:
        for leaf in selection_set.selections:
            if leaf.kind == 'field':
                field.update({
                    leaf.name.value: collect_query_fields(leaf, fragments)
                })
            elif leaf.kind == 'fragment_spread':
                field.update(collect_query_fields(fragments[leaf['name']['value']],
                                                  fragments))
            elif leaf.kind == 'inline_fragment':
                field.update({
                    leaf.type_condition.name.value: collect_query_fields(leaf, fragments)
                })

    return field


def get_query_fields(info):
    """A convenience function to call collect_query_fields with info

    Args:
        info (ResolveInfo)

    Returns:
        dict: Returned from collect_query_fields
    """

    fragments = {}
    node = ast_to_dict(info.field_nodes[0])

    for name, value in info.fragments.items():
        fragments[name] = ast_to_dict(value)

    query = collect_query_fields(node, fragments)
    if "edges" in query:
        return query["edges"]["node"].keys()
    return query


def ast_to_dict(node, include_loc=False):
    if isinstance(node, FieldNode):
        d = {"kind": node.__class__.__name__}
        if hasattr(node, "keys"):
            for field in node.keys:
                d[field] = ast_to_dict(getattr(node, field), include_loc)

        if include_loc and hasattr(node, "loc") and node.loc:
            d["loc"] = {"start": node.loc.start, "end": node.loc.end}

        return d

    elif isinstance(node, list):
        return [ast_to_dict(item, include_loc) for item in node]

    return node


def find_skip_and_limit(first, last, after, before, count):
    reverse = False
    skip = 0
    limit = None
    if first is not None and after is not None:
        skip = after + 1
        limit = first
    elif first is not None and before is not None:
        if first >= before:
            limit = before - 1
        else:
            limit = first
    elif first is not None:
        skip = 0
        limit = first
    elif last is not None and before is not None:
        reverse = False
        if last >= before:
            limit = before
        else:
            limit = last
            skip = before - last
    elif last is not None and after is not None:
        reverse = True
        if last + after < count:
            limit = last
        else:
            limit = count - after - 1
    elif last is not None:
        skip = 0
        limit = last
        reverse = True
    elif after is not None:
        skip = after + 1
    elif before is not None:
        limit = before
    return skip, limit, reverse


def connection_from_iterables(edges, start_offset, has_previous_page, has_next_page, connection_type,
                              edge_type,
                              pageinfo_type):
    edges_items = [
        edge_type(
            node=node,
            cursor=offset_to_cursor((0 if start_offset is None else start_offset) + i)
        )
        for i, node in enumerate(edges)
    ]

    first_edge_cursor = edges_items[0].cursor if edges_items else None
    last_edge_cursor = edges_items[-1].cursor if edges_items else None

    return connection_type(
        edges=edges_items,
        page_info=pageinfo_type(
            start_cursor=first_edge_cursor,
            end_cursor=last_edge_cursor,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page
        )
    )
