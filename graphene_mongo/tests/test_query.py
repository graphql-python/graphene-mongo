import json

import graphene

from graphene.relay import Node

from .models import Article, Editor, Player, Reporter
from .types import (ArticleNode, ArticleType,
                    EditorNode, EditorType,
                    PlayerNode, PlayerType,
                    ReporterNode, ReporterType)
from ..fields import MongoengineConnectionField


def setup_fixtures():
    editor1 = Editor(first_name='Penny', last_name='Hardaway')
    editor1.save()
    editor2 = Editor(first_name='Grant', last_name='Hill')
    editor2.save()
    editor3 = Editor(first_name='Dennis', last_name='Rodman')
    editor3.save()

    reporter = Reporter(first_name='Allen', last_name='Iverson',
                        email='ai@gmail.com',  awards=['2010-mvp'])
    article1 = Article(headline='Hello', editor=editor1)
    article1.save()
    article2 = Article(headline='World', editor=editor2)
    article2.save()

    reporter.articles = [article1, article2]
    reporter.save()

    player1 = Player(first_name='Michael', last_name='Jordan')
    player1.save()
    player2 = Player(first_name='Magic', last_name='Johnson', opponent=player1)
    player2.save()
    player3 = Player(first_name='Larry', last_name='Bird', players=[player1, player2])
    player3.save()

    player1.players = [player2]
    player1.save()

    player2.players = [player1]
    player2.save()


setup_fixtures()


def get_nodes(data, key):
    return map(lambda edge: edge['node'], data[key]['edges'])


def test_should_query_editor_well():

    class Query(graphene.ObjectType):
       editor = graphene.Field(EditorType)
       editors = graphene.List(EditorType)

       def resolve_editor(self, *args, **kwargs):
           return Editor.objects.first()

       def resolve_editors(self, *args, **kwargs):
           return list(Editor.objects.all())

    query = '''
        query EditorQuery {
            editor {
                firstName
            }
            editors {
                firstName,
                lastName
            }
        }
    '''
    expected = {
        'editor': {
            'firstName': 'Penny'
        },
        'editors': [{
            'firstName': 'Penny',
            'lastName': 'Hardaway'
        }, {
            'firstName': 'Grant',
            'lastName': 'Hill'
        }, {
            'firstName': 'Dennis',
            'lastName': 'Rodman'
        }]
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['editor']) == expected['editor']
    assert all(item in result.data['editors'] for item in expected['editors'])


def test_should_query_reporter_well():

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.objects.first()

    query = '''
        query ReporterQuery {
            reporter {
                firstName,
                lastName,
                email,
                articles {
                    headline
                },
                awards
            }
        }
    '''
    expected = {
        'reporter': {
            'firstName': 'Allen',
            'lastName': 'Iverson',
            'email': 'ai@gmail.com',
            'articles': [
                {'headline': 'Hello'},
                {'headline': 'World'}
            ],
            'awards': ['2010-mvp']
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['reporter']) == expected['reporter']


def test_should_node():

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.objects.first()

    query = '''
        query ReporterQuery {
            reporter {
                firstName,
                articles {
                    edges {
                        node {
                            headline
                        }
                    }
                }
                lastName,
                email
            }
        }
    '''
    expected = {
        'reporter': {
            'firstName': 'Allen',
            'lastName': 'Iverson',
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
            'email': 'ai@gmail.com'
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['reporter']) == expected['reporter']


def test_should_connection_field():

    class Query(graphene.ObjectType):
        node = Node.Field()
        all_editors = MongoengineConnectionField(EditorNode)

    query = '''
        query EditorQuery {
          allEditors {
            edges {
                node {
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
                        'firstName': 'Penny',
                        'lastName': 'Hardaway'
                    }
                },
                {
                    'node': {
                        'firstName': 'Grant',
                        'lastName': 'Hill'
                    }

                },
                {
                    'node': {
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


def test_should_mutate_well():

    class CreateArticle(graphene.Mutation):

        class Arguments:
            headline = graphene.String()

        article = graphene.Field(ArticleNode)

        def mutate(self, info, headline):
            article = Article(
                headline=headline
            )
            article.save()

            return CreateArticle(article=article)


    class Query(graphene.ObjectType):
        node = Node.Field()


    class Mutation(graphene.ObjectType):

        create_article = CreateArticle.Field()

    query = '''
        mutation ArticleCreator {
            createArticle(
                headline: "My Article"
            ) {
                article {
                    headline
                }
            }
        }
    '''
    expected = {
        'createArticle': {
            'article': {
                'headline': 'My Article'
            }
        }
    }
    schema = graphene.Schema(query=Query, mutation=Mutation)
    result = schema.execute(query)
    assert not result.errors
    # assert result.data == expected

def test_should_filter():

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = MongoengineConnectionField(ArticleNode)

    query = '''
        query ArticlesQuery {
            articles(headline: "World") {
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
                        'headline': 'World',
                        'editor': {
                            'firstName': 'Grant'
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


def test_should_first_n():

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
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)

    assert not result.errors
    assert all(item in get_nodes(result.data, 'editors') for item in get_nodes(expected, 'editors'))

def test_should_custom_kwargs():

    class Query(graphene.ObjectType):

        editors = graphene.List(EditorType, first=graphene.Int())

        def resolve_editors(self, *args, **kwargs):
            editors = Editor.objects()
            if 'first' in kwargs:
                editors = editors[:kwargs['first']]
            return list(editors)

    query = '''
        query EditorQuery {
            editors(first: 2) {
                firstName,
                lastName
            }
        }
    '''
    expected = {
        'editors':[
            {
                'firstName': 'Penny',
                'lastName': 'Hardaway'
            },
            {
                'firstName': 'Grant',
                'lastName': 'Hill'
            }
        ]
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert all(item in result.data['editors'] for item in expected['editors'])


def test_should_self_reference():

    class Query(graphene.ObjectType):

        all_players = graphene.List(PlayerType)

        def resolve_all_players(self, *args, **kwargs):
            return Player.objects.all()

    query = '''
        query PlayersQuery {
            allPlayers {
                firstName,
                opponent {
                    firstName
                },
                players {
                    firstName
                }
            }
        }
    '''
    expected = {
        'allPlayers': [
            {
                'firstName': 'Michael',
                'opponent': None,
                'players': [
                    {
                        'firstName': 'Magic'
                    }
                ]
            },
            {
                'firstName': 'Magic',
                'opponent': {
                    'firstName': 'Michael'
                },
                'players': [
                    {
                        'firstName': 'Michael'
                    }
                ]
            },
            {
                'firstName': 'Larry',
                'opponent': None,
                'players': [
                    {
                        'firstName': 'Michael'
                    },
                    {
                        'firstName': 'Magic'
                    }
                ]
            }
        ]
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(expected, sort_keys=True)


def test_should_node_self_reference():

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
                        }
                    }
                }
            ]
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == json.dumps(expected, sort_keys=True)


# TODO:
def test_should_paging():
    pass
