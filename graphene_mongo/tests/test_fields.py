from ..fields import MongoengineConnectionField
from .types import ArticleNode
from .models import Article
from .setup import fixtures
from graphene import String


def test_field_args():
    field = MongoengineConnectionField(ArticleNode)

    field_args = ['id', 'headline', 'pub_date']
    assert set(field.field_args.keys()) == set(field_args)

    reference_args = ['editor', 'reporter']
    assert set(field.reference_args.keys()) == set(reference_args)

    default_args = ['after', 'last', 'first', 'before']
    args = field_args + reference_args + default_args
    assert set(field.args) == set(args)


class MyExtendedConnectionField(MongoengineConnectionField):
    @classmethod
    def before_get_query_filter(cls, args):
        my_headline_arg = args.pop('my_headline_arg', None)
        before_filter_setup = {'headline': my_headline_arg}
        return args, before_filter_setup

    @classmethod
    def after_get_query_filter(cls, queryset, args, before_filter_setup):
        queryset = queryset.filter(headline=before_filter_setup['headline'])
        return queryset, args


def test_before_and_after_hooks(fixtures):
    field = MyExtendedConnectionField(ArticleNode)
    queryset, list_length = field.get_query(Article, {},
                                            **{'my_headline_arg': 'World'})
    assert list_length == 1
    assert queryset[0].headline == 'World'
    print(list_length)
