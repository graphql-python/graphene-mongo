import graphene

from . import types
from .models import Article, Child, Reporter
from ..utils import get_model_fields, get_query_fields, is_valid_mongoengine_model


def test_get_model_fields_no_duplication():
    reporter_fields = get_model_fields(Reporter)
    reporter_name_set = set(reporter_fields)
    assert len(reporter_fields) == len(reporter_name_set)


def test_get_model_fields_excluding():
    reporter_fields = get_model_fields(Reporter, excluding=["first_name", "last_name"])
    reporter_name_set = set(reporter_fields)
    assert all(
        field in reporter_name_set
        for field in [
            "id",
            "email",
            "articles",
            "embedded_articles",
            "embedded_list_articles",
            "awards",
        ]
    )


def test_get_model_relation_fields():
    article_fields = get_model_fields(Article)
    assert all(field in set(article_fields) for field in ["editor", "reporter"])


def test_get_base_model_fields():
    child_fields = get_model_fields(Child)
    assert all(field in set(child_fields) for field in ["bar", "baz"])


def test_is_valid_mongoengine_mode():
    assert is_valid_mongoengine_model(Reporter)


def test_get_query_fields():
    # Grab ResolveInfo objects from resolvers and set as nonlocal variables outside
    # Can't assert within resolvers, as the resolvers may not be run if there is an exception
    class Query(graphene.ObjectType):
        child = graphene.Field(types.ChildType)
        children = graphene.List(types.ChildUnionType)

        def resolve_child(self, info, *args, **kwargs):
            test_get_query_fields.child_info = info

        def resolve_children(self, info, *args, **kwargs):
            test_get_query_fields.children_info = info

    query = """
        query Query {
            child {
                bar
                ...testFragment
            }
            children {
                ... on ChildType{
                    baz
                    ...testFragment
                }
                ... on AnotherChildType {
                    qux
                }
            }
        }

        fragment testFragment on ChildType {
            loc {
                type
                coordinates
            }
        }
    """

    schema = graphene.Schema(query=Query)
    schema.execute(query)

    assert get_query_fields(test_get_query_fields.child_info) == {
        "bar": {},
        "loc": {
            "type": {},
            "coordinates": {},
        },
    }

    assert get_query_fields(test_get_query_fields.children_info) == {
        "ChildType": {
            "baz": {},
            "loc": {
                "type": {},
                "coordinates": {},
            },
        },
        "AnotherChildType": {
            "qux": {},
        },
    }
