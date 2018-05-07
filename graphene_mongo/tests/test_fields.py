from ..fields import MongoengineConnectionField
from .types import ArticleNode


def test_field_args():
    field = MongoengineConnectionField(ArticleNode)

    field_args = ['id', 'headline', 'pub_date']
    assert set(field.field_args.keys()) == set(field_args)

    reference_args = ['editor', 'reporter']
    assert set(field.reference_args.keys()) == set(reference_args)

    default_args = ['after', 'last', 'first', 'before']
    args = field_args + reference_args + default_args
    assert set(field.args) == set(args)
