import pytest

from . import nodes, nodes_async
from .. import AsyncMongoengineConnectionField
from ..fields import MongoengineConnectionField


def test_article_field_args():
    field = MongoengineConnectionField(nodes.ArticleNode)

    field_args = {"id", "headline", "pub_date"}
    assert set(field.field_args.keys()) == field_args

    reference_args = {"editor", "reporter"}
    assert all(item in set(field.advance_args.keys()) for item in reference_args)

    default_args = {"after", "last", "first", "before"}
    args = field_args | reference_args | default_args
    assert set(field.args) == args


def test_reporter_field_args():
    field = MongoengineConnectionField(nodes.ReporterNode)

    field_args = {"id", "first_name", "last_name", "email", "awards"}
    assert set(field.field_args.keys()) == field_args


def test_editor_field_args():
    field = MongoengineConnectionField(nodes.EditorNode)

    field_args = {"id", "first_name", "last_name", "metadata", "seq"}
    assert set(field.field_args.keys()) == field_args


def test_field_args_with_property():
    field = MongoengineConnectionField(nodes.PublisherNode)

    field_args = ["id", "name"]
    assert set(field.field_args.keys()) == set(field_args)


def test_field_args_with_unconverted_field():
    field = MongoengineConnectionField(nodes.PublisherNode)

    field_args = ["id", "name"]
    assert set(field.field_args.keys()) == set(field_args)


@pytest.mark.asyncio
async def test_default_resolver_with_colliding_objects_field_async():
    field = AsyncMongoengineConnectionField(nodes_async.ErroneousModelAsyncNode)

    connection = await field.default_resolver(None, {})
    assert 0 == len(connection.iterable)


@pytest.mark.asyncio
async def test_default_resolver_connection_list_length_async(fixtures):
    field = AsyncMongoengineConnectionField(nodes_async.ArticleAsyncNode)

    connection = await field.default_resolver(None, {}, **{"first": 1})
    assert hasattr(connection, "list_length")
    assert connection.list_length == 1
