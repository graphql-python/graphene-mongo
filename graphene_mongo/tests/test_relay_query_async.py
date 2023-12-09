import base64
import json
import os

import graphene
import pytest
from graphene.relay import Node
from graphql_relay.node.node import to_global_id

from . import models
from . import nodes_async
from .. import AsyncMongoengineConnectionField, AsyncMongoengineObjectType


@pytest.mark.asyncio
async def test_should_query_reporter_async(fixtures):
    class Query(graphene.ObjectType):
        reporter = graphene.Field(nodes_async.ReporterAsyncNode)

        async def resolve_reporter(self, *args, **kwargs):
            return models.Reporter.objects.no_dereference().first()

    query = """
        query ReporterQuery {
            reporter {
                firstName,
                lastName,
                email,
                awards,
                articles {
                    edges {
                        node {
                            headline
                        }
                    }
                },
                embeddedArticles {
                    edges {
                        node {
                            headline
                        }
                    }
                },
                embeddedListArticles {
                    edges {
                        node {
                            headline
                        }
                    }
                },
                genericReference {
                    __typename
                    ... on ArticleAsyncNode {
                        headline
                    }
                }
            }
        }
    """
    expected = {
        "reporter": {
            "firstName": "Allen",
            "lastName": "Iverson",
            "email": "ai@gmail.com",
            "awards": ["2010-mvp"],
            "articles": {
                "edges": [
                    {"node": {"headline": "Hello"}},
                    {"node": {"headline": "World"}},
                ]
            },
            "embeddedArticles": {
                "edges": [
                    {"node": {"headline": "Real"}},
                    {"node": {"headline": "World"}},
                ]
            },
            "embeddedListArticles": {
                "edges": [
                    {"node": {"headline": "World"}},
                    {"node": {"headline": "Real"}},
                ]
            },
            "genericReference": {"__typename": "ArticleAsyncNode", "headline": "Hello"},
        }
    }

    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_query_reporters_with_nested_document_async(fixtures):
    class Query(graphene.ObjectType):
        reporters = AsyncMongoengineConnectionField(nodes_async.ReporterAsyncNode)

    query = """
        query ReporterQuery {
            reporters(firstName: "Allen") {
                edges {
                    node {
                        firstName,
                        lastName,
                        email,
                        articles(headline: "Hello") {
                             edges {
                                  node {
                                       headline
                                  }
                             }
                        }
                    }
                }
            }
        }
    """
    expected = {
        "reporters": {
            "edges": [
                {
                    "node": {
                        "firstName": "Allen",
                        "lastName": "Iverson",
                        "email": "ai@gmail.com",
                        "articles": {"edges": [{"node": {"headline": "Hello"}}]},
                    }
                }
            ]
        }
    }

    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_query_all_editors_async(fixtures, fixtures_dirname):
    class Query(graphene.ObjectType):
        editors = AsyncMongoengineConnectionField(nodes_async.EditorAsyncNode)

    query = """
        query EditorQuery {
            editors {
                edges {
                    node {
                        id,
                        firstName,
                        lastName,
                        avatar {
                            contentType,
                            length,
                            data
                        }
                    }
                }
            }
        }
    """

    avator_filename = os.path.join(fixtures_dirname, "image.jpg")
    with open(avator_filename, "rb") as f:
        data = base64.b64encode(f.read())

    expected = {
        "editors": {
            "edges": [
                {
                    "node": {
                        "id": "RWRpdG9yQXN5bmNOb2RlOjE=",
                        "firstName": "Penny",
                        "lastName": "Hardaway",
                        "avatar": {
                            "contentType": "image/jpeg",
                            "length": 46928,
                            "data": data.decode("utf-8"),
                        },
                    }
                },
                {
                    "node": {
                        "id": "RWRpdG9yQXN5bmNOb2RlOjI=",
                        "firstName": "Grant",
                        "lastName": "Hill",
                        "avatar": {"contentType": None, "length": 0, "data": None},
                    }
                },
                {
                    "node": {
                        "id": "RWRpdG9yQXN5bmNOb2RlOjM=",
                        "firstName": "Dennis",
                        "lastName": "Rodman",
                        "avatar": {"contentType": None, "length": 0, "data": None},
                    }
                },
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_query_editors_with_dataloader_async(fixtures):
    from promise import Promise
    from promise.dataloader import DataLoader

    class ArticleLoader(DataLoader):
        def batch_load_fn(self, instances):
            queryset = models.Article.objects(editor__in=instances)
            return Promise.resolve(
                [[a for a in queryset if a.editor.id == instance.id] for instance in instances]
            )

    article_loader = ArticleLoader()

    class _EditorNode(AsyncMongoengineObjectType):
        class Meta:
            model = models.Editor
            interfaces = (graphene.Node,)

        articles = AsyncMongoengineConnectionField(nodes_async.ArticleAsyncNode)

        async def resolve_articles(self, *args, **kwargs):
            return article_loader.load(self)

    class Query(graphene.ObjectType):
        editors = AsyncMongoengineConnectionField(_EditorNode)

    query = """
        query EditorPromiseConnectionQuery {
            editors(first: 1) {
                edges {
                    node {
                        firstName,
                        articles(first: 1) {
                            edges {
                                node {
                                    headline
                                }
                            }
                        }
                    }
                }
            }
        }
    """

    expected = {
        "editors": {
            "edges": [
                {
                    "node": {
                        "firstName": "Penny",
                        "articles": {"edges": [{"node": {"headline": "Hello"}}]},
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_editors_by_id_async(fixtures):
    class Query(graphene.ObjectType):
        editors = AsyncMongoengineConnectionField(nodes_async.EditorAsyncNode)

    query = """
        query EditorQuery {
          editors(id: "RWRpdG9yQXN5bmNOb2RlOjI=") {
            edges {
                node {
                    id,
                    firstName,
                    lastName
                }
            }
          }
        }
    """
    expected = {
        "editors": {
            "edges": [
                {
                    "node": {
                        "id": "RWRpdG9yQXN5bmNOb2RlOjI=",
                        "firstName": "Grant",
                        "lastName": "Hill",
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_async(fixtures):
    class Query(graphene.ObjectType):
        articles = AsyncMongoengineConnectionField(nodes_async.ArticleAsyncNode)

    query = """
        query ArticlesQuery {
            articles(headline: "World") {
                edges {
                    node {
                        headline,
                        pubDate,
                        editor {
                            firstName
                        }
                    }
                }
            }
        }
    """
    expected = {
        "articles": {
            "edges": [
                {
                    "node": {
                        "headline": "World",
                        "editor": {"firstName": "Grant"},
                        "pubDate": "2020-01-01T00:00:00",
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_by_reference_field_async(fixtures):
    class Query(graphene.ObjectType):
        articles = AsyncMongoengineConnectionField(nodes_async.ArticleAsyncNode)

    query = """
        query ArticlesQuery {
            articles(editor: "RWRpdG9yTm9kZTox") {
                edges {
                    node {
                        headline,
                        editor {
                            firstName
                        }
                    }
                }
            }
        }
    """
    expected = {
        "articles": {"edges": [{"node": {"headline": "Hello", "editor": {"firstName": "Penny"}}}]}
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_through_inheritance_async(fixtures):
    class Query(graphene.ObjectType):
        node = Node.Field()
        children = AsyncMongoengineConnectionField(nodes_async.ChildAsyncNode)

    query = """
        query ChildrenQuery {
            children(bar: "bar") {
                edges {
                    node {
                        bar,
                        baz,
                        loc {
                             type,
                             coordinates
                        }
                    }
                }
            }
        }
    """
    expected = {
        "children": {
            "edges": [
                {
                    "node": {
                        "bar": "bar",
                        "baz": "baz",
                        "loc": {"type": "Point", "coordinates": [10.0, 20.0]},
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_by_list_contains_async(fixtures):
    # Notes: https://goo.gl/hMNRgs
    class Query(graphene.ObjectType):
        reporters = AsyncMongoengineConnectionField(nodes_async.ReporterAsyncNode)

    query = """
        query ReportersQuery {
            reporters (awards: "2010-mvp") {
                edges {
                    node {
                        id,
                        firstName,
                        awards,
                        genericReferences {
                            __typename
                            ... on ArticleAsyncNode {
                                headline
                            }
                        }
                    }
                }
            }
        }
    """
    expected = {
        "reporters": {
            "edges": [
                {
                    "node": {
                        "id": "UmVwb3J0ZXJBc3luY05vZGU6MQ==",
                        "firstName": "Allen",
                        "awards": ["2010-mvp"],
                        "genericReferences": [
                            {"__typename": "ArticleAsyncNode", "headline": "Hello"}
                        ],
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_by_id_async(fixtures):
    # Notes: https://goo.gl/hMNRgs
    class Query(graphene.ObjectType):
        reporter = Node.Field(nodes_async.ReporterAsyncNode)

    query = """
        query ReporterQuery {
            reporter (id: "UmVwb3J0ZXJBc3luY05vZGU6MQ==") {
                id,
                firstName,
                awards
            }
        }
    """
    expected = {
        "reporter": {
            "id": "UmVwb3J0ZXJBc3luY05vZGU6MQ==",
            "firstName": "Allen",
            "awards": ["2010-mvp"],
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_first_n_async(fixtures):
    class Query(graphene.ObjectType):
        editors = AsyncMongoengineConnectionField(nodes_async.EditorAsyncNode)

    query = """
        query EditorQuery {
            editors(first: 2) {
                edges {
                    cursor,
                    node {
                        firstName
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """
    expected = {
        "editors": {
            "edges": [
                {"cursor": "YXJyYXljb25uZWN0aW9uOjA=", "node": {"firstName": "Penny"}},
                {"cursor": "YXJyYXljb25uZWN0aW9uOjE=", "node": {"firstName": "Grant"}},
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": False,
                "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
                "endCursor": "YXJyYXljb25uZWN0aW9uOjE=",
            },
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_after_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query EditorQuery {
            players(after: "YXJyYXljb25uZWN0aW9uOjA=") {
                edges {
                    cursor,
                    node {
                        firstName
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {"cursor": "YXJyYXljb25uZWN0aW9uOjE=", "node": {"firstName": "Magic"}},
                {"cursor": "YXJyYXljb25uZWN0aW9uOjI=", "node": {"firstName": "Larry"}},
                {"cursor": "YXJyYXljb25uZWN0aW9uOjM=", "node": {"firstName": "Chris"}},
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_before_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query EditorQuery {
            players(before: "YXJyYXljb25uZWN0aW9uOjI=") {
                edges {
                    cursor,
                    node {
                        firstName
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {"firstName": "Michael"},
                },
                {"cursor": "YXJyYXljb25uZWN0aW9uOjE=", "node": {"firstName": "Magic"}},
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_last_n_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query PlayerQuery {
            players(last: 2) {
                edges {
                    cursor,
                    node {
                        firstName
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {"cursor": "YXJyYXljb25uZWN0aW9uOjI=", "node": {"firstName": "Larry"}},
                {"cursor": "YXJyYXljb25uZWN0aW9uOjM=", "node": {"firstName": "Chris"}},
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_self_reference_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query PlayersQuery {
            players {
                edges {
                    node {
                        firstName,
                        players {
                            edges {
                                node {
                                    firstName
                                }
                            }
                        },
                        embeddedListArticles {
                            edges {
                                node {
                                    headline
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {
                    "node": {
                        "firstName": "Michael",
                        "players": {"edges": [{"node": {"firstName": "Magic"}}]},
                        "embeddedListArticles": {"edges": []},
                    }
                },
                {
                    "node": {
                        "firstName": "Magic",
                        "players": {"edges": [{"node": {"firstName": "Michael"}}]},
                        "embeddedListArticles": {"edges": []},
                    }
                },
                {
                    "node": {
                        "firstName": "Larry",
                        "players": {
                            "edges": [
                                {"node": {"firstName": "Michael"}},
                                {"node": {"firstName": "Magic"}},
                            ]
                        },
                        "embeddedListArticles": {"edges": []},
                    }
                },
                {
                    "node": {
                        "firstName": "Chris",
                        "players": {"edges": []},
                        "embeddedListArticles": {"edges": []},
                    }
                },
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_lazy_reference_async(fixtures):
    class Query(graphene.ObjectType):
        node = Node.Field()
        parents = AsyncMongoengineConnectionField(nodes_async.ParentWithRelationshipAsyncNode)

    schema = graphene.Schema(query=Query)
    print(schema)

    query = """
    query {
        parents {
            edges {
                node {
                    beforeChild {
                        edges {
                            node {
                                name,
                                parent { name }
                            }
                        }
                    },
                    afterChild {
                        edges {
                            node {
                                name,
                                parent { name }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    expected = {
        "parents": {
            "edges": [
                {
                    "node": {
                        "beforeChild": {
                            "edges": [{"node": {"name": "Akari", "parent": {"name": "Yui"}}}]
                        },
                        "afterChild": {
                            "edges": [{"node": {"name": "Kyouko", "parent": {"name": "Yui"}}}]
                        },
                    }
                }
            ]
        }
    }

    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_query_with_embedded_document_async(fixtures):
    class Query(graphene.ObjectType):
        professors = AsyncMongoengineConnectionField(nodes_async.ProfessorVectorAsyncNode)

    query = """
    query {
        professors {
            edges {
                node {
                    vec,
                    metadata {
                        firstName
                    }
                }
            }
        }
    }
    """
    expected = {
        "professors": {
            "edges": [{"node": {"vec": [1.0, 2.3], "metadata": {"firstName": "Steven"}}}]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_get_queryset_returns_dict_filters_async(fixtures):
    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = AsyncMongoengineConnectionField(
            nodes_async.ArticleAsyncNode,
            get_queryset=lambda *_, **__: {"headline": "World"},
        )

    query = """
           query ArticlesQuery {
               articles {
                   edges {
                       node {
                           headline,
                           pubDate,
                           editor {
                               firstName
                           }
                       }
                   }
               }
           }
       """
    expected = {
        "articles": {
            "edges": [
                {
                    "node": {
                        "headline": "World",
                        "editor": {"firstName": "Grant"},
                        "pubDate": "2020-01-01T00:00:00",
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_get_queryset_returns_qs_filters_async(fixtures):
    def get_queryset(model, info, **args):
        return model.objects(headline="World")

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = AsyncMongoengineConnectionField(
            nodes_async.ArticleAsyncNode, get_queryset=get_queryset
        )

    query = """
           query ArticlesQuery {
               articles {
                   edges {
                       node {
                           headline,
                           pubDate,
                           editor {
                               firstName
                           }
                       }
                   }
               }
           }
       """
    expected = {
        "articles": {
            "edges": [
                {
                    "node": {
                        "headline": "World",
                        "editor": {"firstName": "Grant"},
                        "pubDate": "2020-01-01T00:00:00",
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_mongoengine_queryset_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query players {
            players(firstName_Istartswith: "M") {
                edges {
                    node {
                        firstName
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {"node": {"firstName": "Michael"}},
                {"node": {"firstName": "Magic"}},
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(expected, sort_keys=True)


@pytest.mark.asyncio
async def test_should_query_document_with_embedded_async(fixtures):
    class Query(graphene.ObjectType):
        foos = AsyncMongoengineConnectionField(nodes_async.FooAsyncNode)

        async def resolve_multiple_foos(self, *args, **kwargs):
            return list(models.Foo.objects.all())

    query = """
        query {
            foos {
                edges {
                    node {
                        bars {
                            edges {
                                node {
                                    someListField
                                }
                            }
                        }
                    }
                }
            }
        }
    """

    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)
    assert not result.errors


@pytest.mark.asyncio
async def test_should_filter_mongoengine_queryset_with_list_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query players {
            players(firstName_In: ["Michael", "Magic"]) {
                edges {
                    node {
                        firstName
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {"node": {"firstName": "Michael"}},
                {"node": {"firstName": "Magic"}},
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(expected, sort_keys=True)


@pytest.mark.asyncio
async def test_should_get_correct_list_of_documents_async(fixtures):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    query = """
        query players {
            players(firstName: "Michael") {
                edges {
                    node {
                        firstName,
                        articles(first: 3) {
                            edges {
                                node {
                                    headline
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    expected = {
        "players": {
            "edges": [
                {
                    "node": {
                        "firstName": "Michael",
                        "articles": {
                            "edges": [
                                {
                                    "node": {
                                        "headline": "Hello",
                                    }
                                },
                                {
                                    "node": {
                                        "headline": "World",
                                    }
                                },
                            ]
                        },
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_filter_mongoengine_queryset_by_id_and_other_fields_async(
    fixtures,
):
    class Query(graphene.ObjectType):
        players = AsyncMongoengineConnectionField(nodes_async.PlayerAsyncNode)

    larry = models.Player.objects.get(first_name="Larry")
    larry_relay_id = to_global_id("PlayerAsyncNode", larry.id)

    # "Larry" id && firstName == "Michael" should return nothing
    query = """
        query players {{
            players(
                id: "{larry_relay_id}",
                firstName: "Michael"
            ) {{
                edges {{
                    node {{
                        id
                        firstName
                    }}
                }}
            }}
        }}
    """.format(larry_relay_id=larry_relay_id)

    expected = {"players": {"edges": []}}
    schema = graphene.Schema(query=Query)
    result = await schema.execute_async(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(expected, sort_keys=True)
