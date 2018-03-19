import json

import graphene

from .fixtures import setup_fixtures
from .models import Article, Editor, Player, Reporter
from .types import (ArticleNode, ArticleType,
                    EditorNode, EditorType,
                    PlayerNode, PlayerType,
                    ReporterNode, ReporterType)
from ..fields import MongoengineConnectionField

setup_fixtures()


def test_should_query_editor():

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


def test_should_query_reporter():

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
                embeddedArticles {
                    headline
                },
                embeddedListArticles {
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
            'embeddedArticles': [
                {
                    'headline': 'Real'
                },
                {
                    'headline': 'World'
                }
            ],
            'embeddedListArticles': [
                {
                    'headline': 'World'
                },
                {
                    'headline': 'Real'
                }
            ],
            'awards': ['2010-mvp']
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['reporter']) == expected['reporter']


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


# TODO:
def test_should_paging():
    pass
