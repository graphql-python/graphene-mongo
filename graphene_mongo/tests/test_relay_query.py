import json

import graphene

from graphene.relay import Node

from .setup import fixtures
from .models import Article, Reporter
from .types import (ArticleNode,
                    EditorNode,
                    PlayerNode,
                    ReporterNode,
                    ChildNode,
                    ParentWithRelationshipNode)
from ..fields import MongoengineConnectionField


def get_nodes(data, key):
    return map(lambda edge: edge['node'], data[key]['edges'])


def test_should_query_reporter(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.objects.first()

    query = '''
        query ReporterQuery {
            reporter {
                firstName,
                lastName,
                email,
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
                }
            }
        }
    '''
    expected = {
        'reporter': {
            'firstName': 'Allen',
            'lastName': 'Iverson',
            'email': 'ai@gmail.com',
            'articles': {
                'edges': [
                    {
                        'node': {
                            'headline': 'Hello'
                        }
                    },
                    {
                        'node': {
                            'headline': 'World'
                        }
                    }
                ],
            },
            'embeddedArticles': {
                'edges': [
                    {
                        'node': {
                            'headline': 'Real'
                        }
                    },
                    {
                        'node': {
                            'headline': 'World'
                        }
                    }
                ],
            },
            'embeddedListArticles': {
                'edges': [
                    {
                        'node': {
                            'headline': 'World'
                        }
                    },
                    {
                        'node': {
                            'headline': 'Real'
                        }
                    }
                ],
            }
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['reporter']) == expected['reporter']


def test_should_query_all_editors(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        all_editors = MongoengineConnectionField(EditorNode)

    query = '''
        query EditorQuery {
          allEditors {
            edges {
                node {
                    id,
                    firstName,
                    lastName
                }
            }
          }
        }
    '''
    expected = {
        'allEditors': {
            'edges': [
                {
                    'node': {
                        'id': 'RWRpdG9yTm9kZTox',
                        'firstName': 'Penny',
                        'lastName': 'Hardaway'
                    }
                },
                {
                    'node': {
                        'id': 'RWRpdG9yTm9kZToy',
                        'firstName': 'Grant',
                        'lastName': 'Hill'
                    }

                },
                {
                    'node': {
                        'id': 'RWRpdG9yTm9kZToz',
                        'firstName': 'Dennis',
                        'lastName': 'Rodman'
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['allEditors']) == expected['allEditors']


def test_should_filter_editors_by_id(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        all_editors = MongoengineConnectionField(EditorNode)

    query = '''
        query EditorQuery {
          allEditors(id: "RWRpdG9yTm9kZToy") {
            edges {
                node {
                    id,
                    firstName,
                    lastName
                }
            }
          }
        }
    '''
    expected = {
        'allEditors': {
            'edges': [
                {
                    'node': {
                        'id': 'RWRpdG9yTm9kZToy',
                        'firstName': 'Grant',
                        'lastName': 'Hill'
                    }

                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['allEditors']) == expected['allEditors']


def test_should_filter(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = MongoengineConnectionField(ArticleNode)

    query = '''
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
    '''
    expected = {
        'articles': {
            'edges': [
                {
                    'node': {
                        'headline': 'World',
                        'editor': {
                            'firstName': 'Grant'
                        },
                        'pubDate': '2020-01-01T00:00:00'
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_filter_by_reference_field(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = MongoengineConnectionField(ArticleNode)

    query = '''
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
    '''
    expected = {
        'articles': {
            'edges': [
                {
                    'node': {
                        'headline': 'Hello',
                        'editor': {
                            'firstName': 'Penny'
                        }
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_filter_through_inheritance(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        children = MongoengineConnectionField(ChildNode)

    query = '''
        query ChildrenQuery {
            children(bar: "bar") {
                edges {
                    node {
                        bar,
                        baz,
                        loc
                    }
                }
            }
        }
    '''
    expected = {
        'children': {
            'edges': [
                {
                    'node': {
                        'bar': 'bar',
                        'baz': 'baz',
                    }
                }
            ]
        }
    }
    loc = {
         'type': 'Point',
         'coordinates': [10, 20]
    }
    loc_json_string = json.dumps(loc, sort_keys=True)
    schema = graphene.Schema(query=Query)

    result = schema.execute(query)
    result_loc = json.loads(result.data['children']['edges'][0]['node'].pop('loc'))
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(
        expected, sort_keys=True)
    assert json.dumps(result_loc, sort_keys=True) == loc_json_string


def test_should_get_node_by_id(fixtures):
    # Notes: https://goo.gl/hMNRgs
    class Query(graphene.ObjectType):
        reporter = Node.Field(ReporterNode)
        reporters = MongoengineConnectionField(ReporterNode)

    query = '''
        query ReportersQuery {
            reporter (id: "UmVwb3J0ZXJOb2RlOjE=") {
                id,
                firstName
            }
        }
    '''
    expected = {
        'reporter': {
            'id': 'UmVwb3J0ZXJOb2RlOjE=',
            'firstName': 'Allen'
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_first_n(fixtures):

    class Query(graphene.ObjectType):

        editors = MongoengineConnectionField(EditorNode)

    query = '''
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
    '''
    expected = {
        'editors': {
            'edges': [
                {
                    'cursor': 'xxx',
                    'node': {
                        'firstName': 'Penny'
                    }
                },
                {
                    'cursor': 'xxx',
                    'node': {
                        'firstName': 'Grant'
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': True,
                'hasPreviousPage': False,
                'startCursor': 'xxx',
                'endCursor': 'xxx'
            }
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)

    assert not result.errors
    assert all(item in get_nodes(result.data, 'editors')
               for item in get_nodes(expected, 'editors'))


def test_should_after(fixtures):
    class Query(graphene.ObjectType):

        players = MongoengineConnectionField(PlayerNode)

    query = '''
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
    '''
    expected = {
        'players': {
            'edges': [
                {
                    'cursor': 'YXJyYXljb25uZWN0aW9uOjE=',
                    'node': {
                        'firstName': 'Magic',
                    }
                },
                {
                    'cursor': 'YXJyYXljb25uZWN0aW9uOjI=',
                    'node': {
                        'firstName': 'Larry'
                    }
                },
                {
                     'cursor': 'YXJyYXljb25uZWN0aW9uOjM=',
                     'node': {
                        'firstName': 'Chris'
                     }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(
        expected, sort_keys=True)


def test_should_before(fixtures):
    class Query(graphene.ObjectType):

        players = MongoengineConnectionField(PlayerNode)

    query = '''
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
    '''
    expected = {
        'players': {
            'edges': [
                {
                    'cursor': "YXJyYXljb25uZWN0aW9uOjA=",
                    'node': {
                        'firstName': 'Michael',
                    }
                },
                {
                    'cursor': 'YXJyYXljb25uZWN0aW9uOjE=',
                    'node': {
                        'firstName': 'Magic',
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(
        expected, sort_keys=True)


def test_should_last_n(fixtures):
    class Query(graphene.ObjectType):
        players = MongoengineConnectionField(PlayerNode)

    query = '''
        query EditorQuery {
            players(last: 2) {
                edges {
                    cursor,
                    node {
                        firstName
                    }
                }
            }
        }
    '''
    expected = {
        'players': {
            'edges': [
                {
                    'cursor': 'YXJyYXljb25uZWN0aW9uOjI=',
                    'node': {
                        'firstName': 'Larry',
                    }
                },
                {
                     'cursor': 'YXJyYXljb25uZWN0aW9uOjM=',
                     'node': {
                          'firstName': 'Chris'
                     }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)

    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)


def test_should_self_reference(fixtures):

    class Query(graphene.ObjectType):

        all_players = MongoengineConnectionField(PlayerNode)

    query = '''
        query PlayersQuery {
            allPlayers {
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
    '''
    expected = {
        'allPlayers': {
            'edges': [
                {
                    'node': {
                        'firstName': 'Michael',
                        'players': {
                            'edges': [
                                {
                                    'node': {
                                        'firstName': 'Magic'
                                    }
                                }
                            ]
                        },
                        'embeddedListArticles': {
                            'edges': []
                        }
                    }
                },
                {
                    'node': {
                        'firstName': 'Magic',
                        'players': {
                            'edges': [
                                {
                                    'node': {
                                        'firstName': 'Michael'
                                    }
                                }
                            ]
                        },
                        'embeddedListArticles': {
                            'edges': []
                        }

                    }
                },
                {
                    'node': {
                        'firstName': 'Larry',
                        'players': {
                            'edges': [
                                {
                                    'node': {
                                        'firstName': 'Michael'
                                    }
                                },
                                {
                                    'node': {
                                        'firstName': 'Magic'
                                    }
                                }
                            ]
                        },
                        'embeddedListArticles': {
                            'edges': []
                        }
                    }
                },
                {
                     'node': {
                          'firstName': 'Chris',
                          'players': {
                              'edges': []
                          },
                          'embeddedListArticles': {
                               'edges': []
                          }
                     }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(
        expected, sort_keys=True)


def test_should_lazy_reference(fixtures):

    class Query(graphene.ObjectType):
        node = Node.Field()
        parents = MongoengineConnectionField(ParentWithRelationshipNode)

    schema = graphene.Schema(query=Query)

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
                {"node": {
                    "beforeChild": {
                        "edges": [
                            {"node": {
                                "name": "Akari",
                                "parent": {"name": "Yui"}
                            }}
                        ]
                    },
                    "afterChild": {
                        "edges": [
                            {"node": {
                                "name": "Kyouko",
                                "parent": {"name": "Yui"}
                            }}
                        ]
                    }
                }}
            ]
        }
    }

    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(
        expected, sort_keys=True)
