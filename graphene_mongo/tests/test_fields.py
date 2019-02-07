from ..fields import MongoengineConnectionField
from .types import ArticleNode, PublisherNode, ErroneousModelNode


def test_field_args():
    field = MongoengineConnectionField(ArticleNode)

    field_args = ['id', 'headline', 'pub_date']
    assert set(field.field_args.keys()) == set(field_args)

    reference_args = ['editor', 'reporter']
    assert set(field.reference_args.keys()) == set(reference_args)

    default_args = ['after', 'last', 'first', 'before']
    args = field_args + reference_args + default_args
    assert set(field.args) == set(args)


def test_field_args_with_property():
    field = MongoengineConnectionField(PublisherNode)

    field_args = ['id', 'name']
    assert set(field.field_args.keys()) == set(field_args)


def test_field_args_with_unconverted_field():
    field = MongoengineConnectionField(PublisherNode)

    field_args = ['id', 'name']
    assert set(field.field_args.keys()) == set(field_args)


def test_default_resolver_with_colliding_objects_field():
    field = MongoengineConnectionField(ErroneousModelNode)

    connection = field.default_resolver(None, {})
    assert 0 == len(connection.iterable)
